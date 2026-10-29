"""Dhruva.AI V2 — Authentication & Session Management Application Service.

Implements:
- Argon2id credential verification
- Rate-limited login protection
- Dual-token session issuance (short-lived JWT + rotating refresh token)
- Token revocation and logout
- Account status enforcement (rejecting suspended/inactive users)
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.audit.audit_service import AuditService
from src.core.config import get_settings
from src.core.errors import (
    AccountSuspendedError,
    AuthenticationError,
    ConflictError,
    RateLimitExceededError,
)
from src.core.rate_limit import rate_limiter
from src.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    validate_password_strength,
    verify_password,
)
from src.domain.identity.models import User
from src.domain.identity.roles import SystemRole, get_permissions_for_role
from src.infrastructure.persistence.postgres.base import utc_now
from src.infrastructure.repositories.user_repository import UserRepository


settings = get_settings()


class AuthService:
    """Core Authentication and Token Lifecycle Service."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = UserRepository(session)
        self.audit_service = AuditService(session)

    async def login(
        self,
        email: str,
        password: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Tuple[User, str, str, int]:
        """Authenticate user and issue access and refresh tokens.

        Returns:
            Tuple[User, access_token, refresh_token, access_token_expires_in_seconds]
        """
        clean_email = email.strip().lower()

        # Enforce brute-force rate limit
        rate_key = f"login:{ip_address or 'anon'}:{clean_email}"
        if rate_limiter.is_rate_limited(rate_key, max_requests=settings.RATE_LIMIT_LOGIN_PER_MINUTE, window_seconds=60):
            raise RateLimitExceededError("Too many login attempts. Please wait 1 minute before retrying.")

        user = await self.repository.get_by_email(clean_email)
        if not user:
            await self.audit_service.log_event(
                action="AUTH_LOGIN_FAILED",
                entity_name="User",
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                new_values={"email": clean_email, "reason": "USER_NOT_FOUND"},
            )
            raise AuthenticationError("Invalid email or password", code="INVALID_CREDENTIALS")

        # Verify password using Argon2id
        if not verify_password(password, user.password_hash):
            await self.audit_service.log_event(
                action="AUTH_LOGIN_FAILED",
                entity_name="User",
                entity_id=user.id,
                institution_id=user.institution_id,
                actor_user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                new_values={"email": clean_email, "reason": "PASSWORD_MISMATCH"},
            )
            raise AuthenticationError("Invalid email or password", code="INVALID_CREDENTIALS")

        # Check account status
        if user.status != "ACTIVE":
            await self.audit_service.log_event(
                action="AUTH_LOGIN_BLOCKED",
                entity_name="User",
                entity_id=user.id,
                institution_id=user.institution_id,
                actor_user_id=user.id,
                ip_address=ip_address,
                user_agent=user_agent,
                request_id=request_id,
                new_values={"status": user.status},
            )
            raise AccountSuspendedError(f"Account is {user.status.lower()}. Access is disabled.")

        # Update last login timestamp
        await self.repository.update_last_login(user.id)

        # Issue session tokens
        access_token, refresh_token_plain, expires_in = await self.issue_tokens(user)

        # Log successful login in audit trail
        await self.audit_service.log_event(
            action="AUTH_LOGIN_SUCCESS",
            entity_name="User",
            entity_id=user.id,
            institution_id=user.institution_id,
            actor_user_id=user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
        )

        return user, access_token, refresh_token_plain, expires_in

    async def issue_tokens(self, user: User) -> Tuple[str, str, int]:
        """Generate access and rotating refresh tokens for an authenticated user."""
        role_codes = [ur.role.code for ur in user.user_roles if ur.role]
        permissions = await self.repository.get_user_permissions(user.id)

        claims: Dict[str, Any] = {
            "email": user.email,
            "institution_id": str(user.institution_id) if user.institution_id else None,
            "roles": role_codes,
            "permissions": list(permissions),
        }
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id),
            claims=claims,
            expires_delta=access_token_expires,
        )

        refresh_token_plain = generate_refresh_token()
        refresh_hash = hash_token(refresh_token_plain)
        refresh_expires = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await self.repository.save_refresh_token(
            user_id=user.id,
            institution_id=user.institution_id,
            token_hash=refresh_hash,
            expires_at=refresh_expires,
        )

        return access_token, refresh_token_plain, int(access_token_expires.total_seconds())

    async def refresh_session(
        self,
        refresh_token_plain: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Tuple[User, str, str, int]:
        """Rotate refresh token and issue new access token."""
        token_hash = hash_token(refresh_token_plain.strip())
        persisted_token = await self.repository.get_refresh_token(token_hash)

        if not persisted_token or persisted_token.is_revoked:
            raise AuthenticationError("Invalid or revoked refresh token", code="INVALID_REFRESH_TOKEN")

        if persisted_token.expires_at < utc_now():
            await self.repository.revoke_refresh_token(token_hash)
            raise AuthenticationError("Refresh token has expired", code="REFRESH_TOKEN_EXPIRED")

        user = await self.repository.get_by_id(persisted_token.user_id)
        if not user or user.status != "ACTIVE":
            raise AccountSuspendedError("User account is inactive or not found")

        # Invalidate the consumed refresh token (token rotation security policy)
        await self.repository.revoke_refresh_token(token_hash)

        # Issue new rotating refresh token
        new_refresh_plain = generate_refresh_token()
        new_refresh_hash = hash_token(new_refresh_plain)
        new_refresh_expires = utc_now() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        await self.repository.save_refresh_token(
            user_id=user.id,
            institution_id=user.institution_id,
            token_hash=new_refresh_hash,
            expires_at=new_refresh_expires,
        )

        # Issue new access token
        role_codes = [ur.role.code for ur in user.user_roles if ur.role]
        permissions = await self.repository.get_user_permissions(user.id)
        claims = {
            "email": user.email,
            "institution_id": str(user.institution_id) if user.institution_id else None,
            "roles": role_codes,
            "permissions": list(permissions),
        }
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=str(user.id),
            claims=claims,
            expires_delta=access_token_expires,
        )

        return user, access_token, new_refresh_plain, int(access_token_expires.total_seconds())

    async def logout(
        self,
        refresh_token_plain: Optional[str],
        user_id: Optional[uuid.UUID] = None,
        institution_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """Revoke refresh token session on user logout."""
        if refresh_token_plain:
            token_hash = hash_token(refresh_token_plain.strip())
            await self.repository.revoke_refresh_token(token_hash)

        if user_id:
            await self.audit_service.log_event(
                action="AUTH_LOGOUT",
                entity_name="User",
                entity_id=user_id,
                institution_id=institution_id,
                actor_user_id=user_id,
                request_id=request_id,
            )

    async def register_user(
        self,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
        role_type: SystemRole,
        institution_id: Optional[uuid.UUID] = None,
        phone: Optional[str] = None,
        actor_user_id: Optional[uuid.UUID] = None,
        request_id: Optional[str] = None,
    ) -> User:
        """Register a new user with password validation and system role assignment."""
        clean_email = email.strip().lower()
        existing = await self.repository.get_by_email(clean_email)
        if existing:
            raise ConflictError(f"Email '{clean_email}' is already registered", code="EMAIL_ALREADY_EXISTS")

        validate_password_strength(password)
        hashed = hash_password(password)

        new_user = User(
            email=clean_email,
            password_hash=hashed,
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            phone=phone.strip() if phone else None,
            status="ACTIVE",
            institution_id=institution_id,
        )
        created_user = await self.repository.create(new_user)

        # Get or create role
        default_perms = list(get_permissions_for_role(role_type))
        role = await self.repository.get_or_create_system_role(
            code=role_type.value,
            name=role_type.value.replace("_", " ").title(),
            permissions=default_perms,
        )

        # Assign role
        user_id = created_user.id
        user_role = await self.repository.assign_role(
            user_id=user_id,
            role_id=role.id,
            institution_id=institution_id,
            granted_by=actor_user_id,
        )
        user_role.role = role
        created_user.user_roles = [user_role]

        await self.audit_service.log_event(
            action="USER_CREATED",
            entity_name="User",
            entity_id=user_id,
            institution_id=institution_id,
            actor_user_id=actor_user_id or user_id,
            new_values={"email": created_user.email, "role": role_type.value},
            request_id=request_id,
        )

        return created_user
