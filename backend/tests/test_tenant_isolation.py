"""Dhruva.AI V2 — Integration Tests: Multi-Tenant Context & Strict Isolation Enforcement.

Tests:
- Tenant retrieval by slug
- Same-tenant authorization verification
- Cross-tenant denial enforcement (User A in Tenant 1 accessing Tenant 2)
- Super Admin global access across all tenants
- Non-existent tenant resolution
"""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.identity.tenant_service import TenantService
from src.core.errors import NotFoundError, TenantIsolationError
from src.domain.identity.models import Institution, User


@pytest.mark.asyncio
class TestTenantIsolation:
    """Validate strict multi-tenant boundary and cross-tenant leakage prevention."""

    async def test_resolve_tenant_by_slug(self, db_session: AsyncSession, seed_data: dict):
        tenant_service = TenantService(db_session)
        inst = await tenant_service.get_by_slug("iit-bombay")

        assert inst is not None
        assert inst.slug == "iit-bombay"
        assert inst.legal_name == "Indian Institute of Technology Bombay"

    async def test_resolve_unknown_tenant_fails(self, db_session: AsyncSession):
        tenant_service = TenantService(db_session)
        with pytest.raises(NotFoundError) as exc:
            await tenant_service.get_by_slug("non-existent-institution")
        assert exc.value.status_code == 404

    async def test_same_tenant_access_allowed(self, db_session: AsyncSession, seed_data: dict):
        tenant_service = TenantService(db_session)
        inst1: Institution = seed_data["inst1"]
        inst_admin: User = seed_data["inst_admin"]

        # User belongs to inst1, accessing inst1 -> must succeed without exception
        await tenant_service.validate_tenant_access(
            user=inst_admin,
            target_institution=inst1,
            request_id="req-test-1",
        )

    async def test_cross_tenant_access_strictly_denied(self, db_session: AsyncSession, seed_data: dict):
        tenant_service = TenantService(db_session)
        inst2: Institution = seed_data["inst2"]
        inst_admin_1: User = seed_data["inst_admin"]  # Belongs to inst1

        # User in inst1 attempting to access inst2 -> must raise TenantIsolationError
        with pytest.raises(TenantIsolationError) as exc:
            await tenant_service.validate_tenant_access(
                user=inst_admin_1,
                target_institution=inst2,
                request_id="req-cross-tenant-violation",
            )
        assert exc.value.code == "TENANT_ACCESS_DENIED"
        assert exc.value.status_code == 403

    async def test_super_admin_can_access_any_tenant(self, db_session: AsyncSession, seed_data: dict):
        tenant_service = TenantService(db_session)
        inst1: Institution = seed_data["inst1"]
        inst2: Institution = seed_data["inst2"]
        super_admin: User = seed_data["super_admin"]  # Platform super admin

        # Super admin can access inst1
        await tenant_service.validate_tenant_access(
            user=super_admin,
            target_institution=inst1,
            request_id="req-super-1",
        )

        # Super admin can also access inst2
        await tenant_service.validate_tenant_access(
            user=super_admin,
            target_institution=inst2,
            request_id="req-super-2",
        )
