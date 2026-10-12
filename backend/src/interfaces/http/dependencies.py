"""Dhruva.AI V2 — FastAPI Security, RBAC & Tenant Scoping Dependencies.

Enforces:
- JWT Bearer token authentication
- Fine-grained permission checks
- Strict tenant resolution & cross-tenant isolation enforcement
- Standardized API response builder
"""

import uuid
from typing import Any, Callable, List, Optional, Set
from fastapi import Depends, Header, HTTPException, Path, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.identity.tenant_service import TenantService
from src.core.errors import AuthenticationError, PermissionDeniedError
from src.core.security import decode_access_token
from src.domain.identity.models import Institution, User
from src.domain.identity.permissions import Permission
from src.domain.identity.roles import SystemRole
from src.infrastructure.persistence.postgres.database import get_db_session, set_db_tenant_context
from src.infrastructure.repositories.user_repository import UserRepository
from src.interfaces.http.schemas.envelope import ApiResponse, PaginationMeta, ResponseMeta


security_bearer = HTTPBearer(auto_error=False)


def get_request_id(request: Request) -> str:
    """Extract request correlation identifier from request state."""
    return getattr(request.state, "request_id", "req_unknown")


def build_response(
    data: Any,
    request: Request,
    pagination: Optional[PaginationMeta] = None,
) -> ApiResponse[Any]:
    """Helper to construct standardized API responses with envelope metadata."""
    request_id = get_request_id(request)
    meta = ResponseMeta(request_id=request_id, pagination=pagination)
    return ApiResponse(success=True, data=data, meta=meta)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Authenticate incoming request via JWT Bearer token or HttpOnly cookie."""
    token: Optional[str] = None
    if credentials:
        token = credentials.credentials
    else:
        # Check fallback cookie
        token = request.cookies.get("access_token")

    if not token:
        raise AuthenticationError("Authorization credentials missing", code="UNAUTHORIZED")

    payload = decode_access_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Invalid token subject", code="INVALID_TOKEN")

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise AuthenticationError("Invalid token subject format", code="INVALID_TOKEN")

    user_repo = UserRepository(session)
    user = await user_repo.get_by_id(user_uuid)
    if not user:
        raise AuthenticationError("User not found or deleted", code="USER_NOT_FOUND")

    if user.status != "ACTIVE":
        raise AuthenticationError(f"Account is {user.status.lower()}", code="ACCOUNT_INACTIVE")

    return user


def require_roles(*allowed_roles: SystemRole) -> Callable:
    """Dependency factory checking that the authenticated user possesses at least one required role."""
    allowed_codes = {r.value for r in allowed_roles}

    async def role_checker(user: User = Depends(get_current_user)) -> User:
        user_roles = {ur.role.code for ur in user.user_roles if ur.role}
        # Super admin always passes
        if SystemRole.SUPER_ADMIN.value in user_roles:
            return user

        if not user_roles.intersection(allowed_codes):
            raise PermissionDeniedError(
                f"Requires one of roles: {', '.join(allowed_codes)}",
                code="INSUFFICIENT_ROLE",
            )
        return user

    return role_checker


def require_permission(permission: Permission) -> Callable:
    """Dependency factory checking that user holds a specific permission."""

    async def permission_checker(
        user: User = Depends(get_current_user),
        session: AsyncSession = Depends(get_db_session),
    ) -> User:
        user_repo = UserRepository(session)
        perms = await user_repo.get_user_permissions(user.id)

        # Super admin bypass
        user_roles = {ur.role.code for ur in user.user_roles if ur.role}
        if SystemRole.SUPER_ADMIN.value in user_roles:
            return user

        if permission.value not in perms:
            raise PermissionDeniedError(
                f"Missing required permission: '{permission.value}'",
                code="INSUFFICIENT_PERMISSION",
            )
        return user

    return permission_checker


async def get_current_tenant(
    request: Request,
    institution_slug: str = Path(..., description="Institution tenant slug identifier"),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> Institution:
    """Resolve and enforce tenant boundary.

    1. Loads institution by path slug.
    2. Enforces that user belongs to this institution (unless SUPER_ADMIN).
    3. Sets PostgreSQL RLS session variable `app.current_institution_id`.
    4. Returns verified Institution object.
    """
    tenant_service = TenantService(session)
    institution = await tenant_service.get_by_slug(institution_slug)

    client_ip = request.client.host if request.client else None
    request_id = get_request_id(request)

    # Enforce isolation
    await tenant_service.validate_tenant_access(
        user=user,
        target_institution=institution,
        request_id=request_id,
        ip_address=client_ip,
    )

    # Set PostgreSQL RLS context
    await set_db_tenant_context(session, str(institution.id))

    return institution
