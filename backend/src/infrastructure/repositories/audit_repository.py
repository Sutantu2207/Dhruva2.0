"""Dhruva.AI V2 — Audit Repository.

Persists append-only security and governance audit log records.
"""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.audit.models import AuditLog


class AuditRepository:
    """Repository for persisting and querying append-only audit records."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, record: AuditLog) -> AuditLog:
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def list_by_institution(
        self,
        institution_id: Optional[uuid.UUID] = None,
        actor_user_id: Optional[uuid.UUID] = None,
        action: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[AuditLog]:
        stmt = select(AuditLog)
        if institution_id:
            stmt = stmt.where(AuditLog.institution_id == institution_id)
        if actor_user_id:
            stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        stmt = stmt.offset(skip).limit(limit).order_by(AuditLog.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
