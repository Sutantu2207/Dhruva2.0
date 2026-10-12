"""Dhruva.AI V2 — Institution Repository.

Handles database queries and persistence operations for institutions/tenants.
"""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.identity.models import Institution


class InstitutionRepository:
    """Repository interface for Institution entity."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, institution_id: uuid.UUID) -> Optional[Institution]:
        stmt = select(Institution).where(Institution.id == institution_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Institution]:
        stmt = select(Institution).where(Institution.slug == slug)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_domain(self, domain: str) -> Optional[Institution]:
        stmt = select(Institution).where(Institution.domain == domain)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, institution: Institution) -> Institution:
        self.session.add(institution)
        await self.session.commit()
        await self.session.refresh(institution)
        return institution

    async def list_all(self, skip: int = 0, limit: int = 50) -> List[Institution]:
        stmt = select(Institution).offset(skip).limit(limit).order_by(Institution.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
