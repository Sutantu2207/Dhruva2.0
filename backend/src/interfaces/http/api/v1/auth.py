"""Dhruva.AI V2 — Authentication & Session API Routes.

Implements:
- POST /auth/register
- POST /auth/login
- POST /auth/refresh
- POST /auth/logout
- GET /auth/me
- GET /auth/institutions
"""

from typing import List, Optional
from fastapi import APIRouter, Cookie, Depends, Header, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.identity.auth_service import AuthService
from src.core.config import get_settings
from src.core.errors import AuthenticationError
from src.domain.identity.models import User
from src.domain.identity.roles import get_permissions_for_role
from src.infrastructure.persistence.postgres.database import get_db_session
from src.infrastructure.repositories.institution_repository import InstitutionRepository
from src.infrastructure.repositories.user_repository import UserRepository
from src.interfaces.http.dependencies import (
    build_response,
    get_current_user,
    get_request_id,
)
from src.interfaces.http.schemas.auth import (
    LoginRequest,
    LoginResponseData,
    RefreshResponseData,
    RefreshTokenRequest,
    RegisterUserRequest,
    UserResponse,
)
from src.interfaces.http.schemas.envelope import ApiResponse
from src.interfaces.http.schemas.tenant import InstitutionResponse


settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set secure, HttpOnly authentication cookies on response."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies on logout."""
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")


@router.get(
    "/institutions",
    response_model=ApiResponse[List[InstitutionResponse]],
    summary="List Active Institutions",
)
async def list_institutions(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[InstitutionResponse]]:
    """List available institutions for registration and onboarding."""
    repo = InstitutionRepository(session)
    insts = await repo.list_all(limit=100)
    data = [InstitutionResponse.model_validate(inst) for inst in insts if inst.status == "ACTIVE"]
    return build_response(data=data, request=request)


@router.post(
    "/register",
    response_model=ApiResponse[LoginResponseData],
    status_code=status.HTTP_201_CREATED,
    summary="Self-Service User Registration",
)
async def register(
    payload: RegisterUserRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[LoginResponseData]:
    """Register a new student or faculty account, issue session tokens, and set secure cookies."""
    auth_service = AuthService(session)
    inst_repo = InstitutionRepository(session)
    request_id = get_request_id(request)

    # 1. Resolve institution
    institution_id = None
    if payload.institution_slug:
        inst = await inst_repo.get_by_slug(payload.institution_slug)
        if not inst:
            raise AuthenticationError(f"Institution '{payload.institution_slug}' not found", code="INSTITUTION_NOT_FOUND")
        institution_id = inst.id
    else:
        # Try domain match
        domain = payload.email.split("@")[-1].lower()
        inst = await inst_repo.get_by_domain(domain)
        if inst:
            institution_id = inst.id
        else:
            # Fallback to first active institution
            active_insts = await inst_repo.list_all(limit=1)
            if active_insts:
                institution_id = active_insts[0].id

    # 2. Register user
    created_user = await auth_service.register_user(
        email=payload.email,
        password=payload.password,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role_type=payload.role,
        institution_id=institution_id,
        phone=payload.phone,
        request_id=request_id,
    )

    # 3. Issue session tokens
    access_token, refresh_token, expires_in = await auth_service.issue_tokens(created_user)
    _set_auth_cookies(response, access_token, refresh_token)

    roles = [ur.role.code for ur in created_user.user_roles if ur.role]
    perms = list(get_permissions_for_role(payload.role))

    user_dto = UserResponse(
        id=created_user.id,
        institution_id=created_user.institution_id,
        institution_slug=inst.slug if inst else None,
        email=created_user.email,
        first_name=created_user.first_name,
        last_name=created_user.last_name,
        full_name=created_user.full_name,
        phone=created_user.phone,
        status=created_user.status,
        roles=roles,
        permissions=perms,
        last_login_at=created_user.last_login_at,
        created_at=created_user.created_at,
    )

    data = LoginResponseData(
        user=user_dto,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )
    return build_response(data=data, request=request)


@router.post(
    "/login",
    response_model=ApiResponse[LoginResponseData],
    summary="Authenticate User & Issue Session",
)
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[LoginResponseData]:
    """Authenticate with email and password. Issues JWT access token and rotating refresh token."""
    auth_service = AuthService(session)
    request_id = get_request_id(request)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    user, access_token, refresh_token, expires_in = await auth_service.login(
        email=payload.email,
        password=payload.password,
        ip_address=client_ip,
        user_agent=user_agent,
        request_id=request_id,
    )

    _set_auth_cookies(response, access_token, refresh_token)

    repo = UserRepository(session)
    perms = await repo.get_user_permissions(user.id)
    roles = [ur.role.code for ur in user.user_roles if ur.role]

    user_dto = UserResponse(
        id=user.id,
        institution_id=user.institution_id,
        institution_slug=user.institution.slug if user.institution else None,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        phone=user.phone,
        status=user.status,
        roles=roles,
        permissions=list(perms),
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )

    data = LoginResponseData(
        user=user_dto,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )
    return build_response(data=data, request=request)


@router.post(
    "/refresh",
    response_model=ApiResponse[RefreshResponseData],
    summary="Rotate Session Refresh Token",
)
async def refresh_token(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenRequest] = None,
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[RefreshResponseData]:
    """Rotate refresh token and issue new access token. Protects against token reuse."""
    token = payload.refresh_token if (payload and payload.refresh_token) else refresh_token_cookie
    if not token:
        raise AuthenticationError("Refresh token missing", code="MISSING_REFRESH_TOKEN")

    auth_service = AuthService(session)
    request_id = get_request_id(request)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("User-Agent")

    user, new_access_token, new_refresh_token, expires_in = await auth_service.refresh_session(
        refresh_token_plain=token,
        ip_address=client_ip,
        user_agent=user_agent,
        request_id=request_id,
    )

    _set_auth_cookies(response, new_access_token, new_refresh_token)

    repo = UserRepository(session)
    perms = await repo.get_user_permissions(user.id)
    roles = [ur.role.code for ur in user.user_roles if ur.role]

    user_dto = UserResponse(
        id=user.id,
        institution_id=user.institution_id,
        institution_slug=user.institution.slug if user.institution else None,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        phone=user.phone,
        status=user.status,
        roles=roles,
        permissions=list(perms),
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )

    data = RefreshResponseData(
        user=user_dto,
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
    )
    return build_response(data=data, request=request)


@router.post(
    "/logout",
    summary="Revoke Session & Logout",
)
async def logout(
    request: Request,
    response: Response,
    payload: Optional[RefreshTokenRequest] = None,
    refresh_token_cookie: Optional[str] = Cookie(None, alias="refresh_token"),
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[dict]:
    """Revoke session refresh token and delete authentication cookies."""
    token = payload.refresh_token if (payload and payload.refresh_token) else refresh_token_cookie
    auth_service = AuthService(session)
    request_id = get_request_id(request)

    await auth_service.logout(
        refresh_token_plain=token,
        user_id=user.id if user else None,
        institution_id=user.institution_id if user else None,
        request_id=request_id,
    )

    _clear_auth_cookies(response)
    return build_response(data={"message": "Logged out successfully"}, request=request)


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Current Authenticated User Profile",
)
async def get_me(
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[UserResponse]:
    """Retrieve identity, tenant membership, roles, and active permissions of caller."""
    repo = UserRepository(session)
    perms = await repo.get_user_permissions(user.id)
    roles = [ur.role.code for ur in user.user_roles if ur.role]

    user_dto = UserResponse(
        id=user.id,
        institution_id=user.institution_id,
        institution_slug=user.institution.slug if user.institution else None,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        full_name=user.full_name,
        phone=user.phone,
        status=user.status,
        roles=roles,
        permissions=list(perms),
        last_login_at=user.last_login_at,
        created_at=user.created_at,
    )
    return build_response(data=user_dto, request=request)
