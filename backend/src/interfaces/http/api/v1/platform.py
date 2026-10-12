"""Dhruva.AI V2 — Platform & System Administration API Routes.

Provides:
- Liveness (/health) and Readiness (/ready) checks with actual DB connectivity telemetry
- Multi-tenant institution creation & management (Super Admin only)
- Platform-wide audit telemetry (Super Admin only)
"""

import time
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.identity.tenant_service import TenantService
from src.domain.identity.models import User
from src.domain.identity.roles import SystemRole
from src.infrastructure.persistence.postgres.database import get_db_session
from src.infrastructure.repositories.audit_repository import AuditRepository
from src.infrastructure.repositories.institution_repository import InstitutionRepository
from src.interfaces.http.dependencies import (
    build_response,
    get_request_id,
    require_roles,
)
from src.interfaces.http.schemas.audit import AuditLogResponse
from src.interfaces.http.schemas.envelope import ApiResponse, PaginationMeta
from src.interfaces.http.schemas.tenant import InstitutionCreateRequest, InstitutionResponse


router = APIRouter(prefix="/platform", tags=["Platform & System Operations"])


@router.get("/health", summary="Liveness Probe")
async def health_check(request: Request) -> ApiResponse[Dict[str, str]]:
    """Liveness probe confirming the API worker is running and processing HTTP requests."""
    return build_response(
        data={"status": "UP", "message": "Dhruva.AI V2 API is live and healthy"},
        request=request,
    )


@router.get("/ready", summary="Readiness Probe")
async def readiness_check(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[Dict[str, Any]]:
    """Readiness probe verifying operational status of mandatory infrastructure (Database)."""
    start_time = time.perf_counter()
    db_status = "UNKNOWN"
    db_latency_ms = 0.0

    try:
        await session.execute(text("SELECT 1"))
        db_latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        db_status = "CONNECTED"
    except Exception as exc:
        db_status = f"FAILED: {str(exc)}"

    is_ready = db_status == "CONNECTED"
    data = {
        "status": "READY" if is_ready else "NOT_READY",
        "infrastructure": {
            "database": {
                "status": db_status,
                "latency_ms": db_latency_ms,
            }
        },
    }
    return build_response(data=data, request=request)


@router.post(
    "/institutions",
    response_model=ApiResponse[InstitutionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Institutional Tenant",
)
async def create_institution(
    payload: InstitutionCreateRequest,
    request: Request,
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[InstitutionResponse]:
    """Create a new institutional tenant partition (Super Admin only)."""
    tenant_service = TenantService(session)
    request_id = get_request_id(request)

    created = await tenant_service.create_institution(
        slug=payload.slug,
        legal_name=payload.legal_name,
        domain=payload.domain,
        actor_user_id=user.id,
        request_id=request_id,
    )
    return build_response(data=InstitutionResponse.model_validate(created), request=request)


@router.get(
    "/institutions",
    response_model=ApiResponse[List[InstitutionResponse]],
    summary="List All Institutional Tenants",
)
async def list_institutions(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[InstitutionResponse]]:
    """List all registered institutional tenants on the platform (Super Admin only)."""
    repo = InstitutionRepository(session)
    institutions = await repo.list_all(skip=skip, limit=limit)
    data = [InstitutionResponse.model_validate(inst) for inst in institutions]
    pagination = PaginationMeta(page=(skip // limit) + 1, page_size=limit, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.get(
    "/audit-logs",
    response_model=ApiResponse[List[AuditLogResponse]],
    summary="Global Audit Logs",
)
async def list_platform_audit_logs(
    request: Request,
    action: str = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[AuditLogResponse]]:
    """Query platform-wide audit events (Super Admin only)."""
    repo = AuditRepository(session)
    records = await repo.list_by_institution(action=action, skip=skip, limit=limit)
    data = [AuditLogResponse.model_validate(r) for r in records]
    pagination = PaginationMeta(page=(skip // limit) + 1, page_size=limit, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)
