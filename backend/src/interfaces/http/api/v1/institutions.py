"""Dhruva.AI V2 — Tenant-Scoped Institutional Operations API Routes.

URL Convention: /api/v1/institutions/{institution_slug}/...
Enforces tenant boundary isolation and granular RBAC.
"""

from typing import List
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.identity.auth_service import AuthService
from src.domain.identity.models import Institution, User
from src.domain.identity.permissions import Permission
from src.domain.identity.roles import SystemRole
from src.infrastructure.persistence.postgres.database import get_db_session
from src.infrastructure.repositories.audit_repository import AuditRepository
from src.infrastructure.repositories.user_repository import UserRepository
from src.interfaces.http.dependencies import (
    build_response,
    get_current_tenant,
    get_current_user,
    get_request_id,
    require_permission,
)
from src.interfaces.http.schemas.audit import AuditLogResponse
from src.interfaces.http.schemas.auth import RegisterUserRequest, UserResponse
from src.interfaces.http.schemas.envelope import ApiResponse, PaginationMeta
from src.interfaces.http.schemas.tenant import InstitutionResponse


router = APIRouter(prefix="/institutions/{institution_slug}", tags=["Tenant Institutional Operations"])


@router.get(
    "",
    response_model=ApiResponse[InstitutionResponse],
    summary="Get Institution Details",
)
async def get_institution_details(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
) -> ApiResponse[InstitutionResponse]:
    """Retrieve tenant institution metadata. Enforces tenant scope matching."""
    return build_response(data=InstitutionResponse.model_validate(tenant), request=request)


@router.get(
    "/users",
    response_model=ApiResponse[List[UserResponse]],
    summary="List Institution Users",
)
async def list_institution_users(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_permission(Permission.INSTITUTION_USERS_MANAGE)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[UserResponse]]:
    """List members belonging to this institution. Strictly isolated by tenant ID."""
    repo = UserRepository(session)
    users = await repo.list_by_institution(institution_id=tenant.id, skip=skip, limit=limit)

    result_users: List[UserResponse] = []
    for u in users:
        perms = await repo.get_user_permissions(u.id)
        roles = [ur.role.code for ur in u.user_roles if ur.role]
        result_users.append(
            UserResponse(
                id=u.id,
                institution_id=u.institution_id,
                email=u.email,
                first_name=u.first_name,
                last_name=u.last_name,
                full_name=u.full_name,
                phone=u.phone,
                status=u.status,
                roles=roles,
                permissions=list(perms),
                last_login_at=u.last_login_at,
                created_at=u.created_at,
            )
        )

    pagination = PaginationMeta(page=(skip // limit) + 1, page_size=limit, total_records=len(result_users))
    return build_response(data=result_users, request=request, pagination=pagination)


@router.post(
    "/users",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Institution User",
)
async def create_institution_user(
    payload: RegisterUserRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(require_permission(Permission.INSTITUTION_USERS_MANAGE)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[UserResponse]:
    """Create and onboard a user scoped to this specific institution."""
    auth_service = AuthService(session)
    request_id = get_request_id(request)

    created = await auth_service.register_user(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role_type=payload.role,
        institution_id=tenant.id,
        phone=payload.phone,
        actor_user_id=caller.id,
        request_id=request_id,
    )

    repo = UserRepository(session)
    perms = await repo.get_user_permissions(created.id)
    roles = [ur.role.code for ur in created.user_roles if ur.role]

    user_dto = UserResponse(
        id=created.id,
        institution_id=created.institution_id,
        email=created.email,
        first_name=created.first_name,
        last_name=created.last_name,
        full_name=created.full_name,
        phone=created.phone,
        status=created.status,
        roles=roles,
        permissions=list(perms),
        last_login_at=created.last_login_at,
        created_at=created.created_at,
    )
    return build_response(data=user_dto, request=request)


@router.get(
    "/audit-logs",
    response_model=ApiResponse[List[AuditLogResponse]],
    summary="Institution Audit Logs",
)
async def list_institution_audit_logs(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(require_permission(Permission.AUDIT_READ_INSTITUTION)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[AuditLogResponse]]:
    """Retrieve audit events scoped strictly to this institution."""
    repo = AuditRepository(session)
    records = await repo.list_by_institution(institution_id=tenant.id, skip=skip, limit=limit)
    data = [AuditLogResponse.model_validate(r) for r in records]
    pagination = PaginationMeta(page=(skip // limit) + 1, page_size=limit, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)
