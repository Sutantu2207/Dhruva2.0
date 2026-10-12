"""Dhruva.AI V2 — Tenant Isolation & Management Service.

Enforces strict tenant scoping, ensures no cross-tenant leakage,
and resolves tenant context dynamically from authorized user identities.
"""

import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.audit.audit_service import AuditService
from src.core.errors import ConflictError, NotFoundError, TenantIsolationError
from src.domain.identity.models import Institution, User
from src.domain.identity.roles import SystemRole
from src.infrastructure.repositories.institution_repository import InstitutionRepository


class TenantService:
    """Service governing multi-tenancy and institutional boundary enforcement."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = InstitutionRepository(session)
        self.audit_service = AuditService(session)

    async def create_institution(
        self,
        slug: str,
        legal_name: str,
        domain: Optional[str] = None,
        actor_user_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> Institution:
        """Create new tenant institution with unique slug."""
        clean_slug = slug.strip().lower()
        existing = await self.repository.get_by_slug(clean_slug)
        if existing:
            raise ConflictError(f"Institution slug '{clean_slug}' is already registered", code="SLUG_ALREADY_EXISTS")

        if domain:
            existing_domain = await self.repository.get_by_domain(domain.strip().lower())
            if existing_domain:
                raise ConflictError(f"Institution domain '{domain}' is already registered", code="DOMAIN_ALREADY_EXISTS")

        institution = Institution(
            slug=clean_slug,
            legal_name=legal_name.strip(),
            domain=domain.strip().lower() if domain else None,
            status="ACTIVE",
            settings={},
        )
        created = await self.repository.create(institution)

        await self.audit_service.log_event(
            action="INSTITUTION_CREATED",
            entity_name="Institution",
            entity_id=created.id,
            institution_id=created.id,
            actor_user_id=actor_user_id,
            new_values={"slug": created.slug, "legal_name": created.legal_name},
            request_id=request_id,
        )
        return created

    async def get_by_slug(self, slug: str) -> Institution:
        """Fetch institution by slug or raise NotFoundError."""
        institution = await self.repository.get_by_slug(slug.strip().lower())
        if not institution:
            raise NotFoundError(resource="Institution", identifier=slug)
        return institution

    async def get_by_id(self, institution_id: uuid.UUID) -> Institution:
        """Fetch institution by ID or raise NotFoundError."""
        institution = await self.repository.get_by_id(institution_id)
        if not institution:
            raise NotFoundError(resource="Institution", identifier=str(institution_id))
        return institution

    async def validate_tenant_access(
        self,
        user: User,
        target_institution: Institution,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Validate whether the user is authorized to access the given target institution.

        Rules:
        - SUPER_ADMIN has global access across all tenants.
        - Institutional users can ONLY access their own assigned institution.
        - Cross-tenant access triggers a TenantIsolationError and records a security audit log.
        """
        user_roles = [ur.role.code for ur in user.user_roles if ur.role]
        if SystemRole.SUPER_ADMIN.value in user_roles:
            return

        if user.institution_id != target_institution.id:
            # Record security violation audit event
            await self.audit_service.log_event(
                action="CROSS_TENANT_ACCESS_DENIED",
                entity_name="Institution",
                entity_id=target_institution.id,
                institution_id=user.institution_id,
                actor_user_id=user.id,
                new_values={
                    "target_institution_id": str(target_institution.id),
                    "user_institution_id": str(user.institution_id) if user.institution_id else None,
                },
                ip_address=ip_address,
                request_id=request_id,
            )
            raise TenantIsolationError(
                f"Unauthorized tenant access: User does not belong to institution '{target_institution.slug}'"
            )
