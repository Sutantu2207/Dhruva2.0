"""Dhruva.AI V2 — User & Identity Repository.

Handles user lookups, credentials, role assignments, and refresh token lifecycle.
"""

import uuid
from datetime import datetime
from typing import List, Optional, Set
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.domain.identity.models import RefreshToken, Role, User, UserRole
from src.domain.identity.permissions import Permission
from src.domain.identity.roles import SystemRole
from src.infrastructure.persistence.postgres.base import utc_now


class UserRepository:
    """Repository interface for User, Role, and Session persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        stmt = (
            select(User)
            .options(
                selectinload(User.institution),
                selectinload(User.user_roles).selectinload(UserRole.role),
            )
            .where(User.id == user_id, User.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        stmt = (
            select(User)
            .options(
                selectinload(User.institution),
                selectinload(User.user_roles).selectinload(UserRole.role),
            )
            .where(User.email == email.lower().strip(), User.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        user.email = user.email.lower().strip()
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=utc_now(), updated_at=utc_now())
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def list_by_institution(
        self, institution_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[User]:
        stmt = (
            select(User)
            .options(selectinload(User.user_roles).selectinload(UserRole.role))
            .where(User.institution_id == institution_id, User.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(User.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # --- Role Operations ---

    async def get_or_create_system_role(
        self, code: str, name: str, permissions: List[str]
    ) -> Role:
        stmt = select(Role).where(Role.code == code, Role.is_system_role.is_(True))
        result = await self.session.execute(stmt)
        role = result.scalar_one_or_none()
        if not role:
            role = Role(
                code=code,
                name=name,
                permissions=permissions,
                is_system_role=True,
                institution_id=None,
            )
            self.session.add(role)
            await self.session.commit()
            await self.session.refresh(role)
        return role

    async def assign_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        institution_id: Optional[uuid.UUID] = None,
        context_department_id: Optional[uuid.UUID] = None,
        granted_by: Optional[uuid.UUID] = None,
    ) -> UserRole:
        # Check if already assigned
        stmt = select(UserRole).where(
            UserRole.user_id == user_id,
            UserRole.role_id == role_id,
            UserRole.institution_id == institution_id,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            institution_id=institution_id,
            context_department_id=context_department_id,
            granted_by=granted_by,
        )
        self.session.add(user_role)
        await self.session.commit()
        await self.session.refresh(user_role)
        return user_role

    async def get_user_permissions(self, user_id: uuid.UUID) -> Set[str]:
        user = await self.get_by_id(user_id)
        if not user:
            return set()
        user_roles = [ur.role.code for ur in user.user_roles if ur.role]
        if SystemRole.SUPER_ADMIN.value in user_roles:
            return {p.value for p in Permission}
        permissions: Set[str] = set()
        for ur in user.user_roles:
            if ur.role and ur.role.permissions:
                for p in ur.role.permissions:
                    permissions.add(p)
        return permissions

    # --- Refresh Token Operations ---

    async def save_refresh_token(
        self,
        user_id: uuid.UUID,
        institution_id: Optional[uuid.UUID],
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            institution_id=institution_id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False,
        )
        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)
        return token

    async def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, token_hash: str) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token_hash == token_hash)
            .values(is_revoked=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> None:
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(is_revoked=True)
        )
        await self.session.execute(stmt)
        await self.session.commit()
