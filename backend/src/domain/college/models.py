"""Dhruva.AI V2 — College & Higher Education Institution Models.

Supports comprehensive directory of colleges across Coimbatore and Tamil Nadu.
"""

import uuid
from typing import Optional
from sqlalchemy import Index, String, Text, Uuid, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.persistence.postgres.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)


class College(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Accredited College or Higher Education Institution."""

    __tablename__ = "colleges"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    institution_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    affiliated_university: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    district: Mapped[str] = mapped_column(String(64), default="Coimbatore", nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(64), default="Tamil Nadu", nullable=False)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    accreditation: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False, index=True)

    __table_args__ = (
        Index("ix_colleges_search", "name", "district", "status"),
        Index("ix_colleges_type", "institution_type", "district"),
    )

    def __repr__(self) -> str:
        return f"<College(name='{self.name}', type='{self.institution_type}', location='{self.location}')>"


class CollegeRequest(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User-submitted unlisted college request pending administrative review."""

    __tablename__ = "college_requests"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    requester_name: Mapped[str] = mapped_column(String(128), nullable=False)
    requester_email: Mapped[str] = mapped_column(String(255), nullable=False)
    college_name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<CollegeRequest(college='{self.college_name}', status='{self.status}')>"
