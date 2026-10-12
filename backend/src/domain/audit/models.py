"""Dhruva.AI V2 — Audit Log Domain Model.

Provides immutable, append-only security and governance audit logs.
Tracks:
- Actor (user UUID or system)
- Institution context
- Action performed
- Entity name and identifier
- State diff (old vs new values)
- Client IP address, User-Agent, and Request Correlation ID
- Exact UTC timestamp
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column
from src.infrastructure.persistence.postgres.base import (
    Base,
    UUIDPrimaryKeyMixin,
    utc_now,
)


class AuditLog(Base, UUIDPrimaryKeyMixin):
    """Immutable Audit Log Record."""

    __tablename__ = "audit_logs"

    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    entity_name: Mapped[str] = mapped_column(String(128), index=True, nullable=False)
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), index=True, nullable=True)
    old_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    new_values: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    __table_args__ = (
        Index("idx_audit_institution_created", "institution_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action={self.action}, actor={self.actor_user_id})>"
