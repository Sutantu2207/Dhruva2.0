"""Dhruva.AI V2 — Interventions, Notifications & Institutional Analytics Domain Models.

Implements the complete Phase 8 schema:
- Intervention: Academic interventions for at-risk students with assigned action plans and tracking.
- Notification: In-app real-time notifications with user-bound isolation and read state management.
- AnalyticsRollup: Pre-computed institutional and departmental metrics rollups for high-performance dashboards.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.persistence.postgres.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utc_now,
)


class Intervention(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Academic intervention assigned to an at-risk student."""

    __tablename__ = "interventions"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    faculty_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    intervention_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # REMEDIAL_SESSION | PEER_TUTORING | ATTENDANCE_WARNING | ACADEMIC_PROBATION | CURRICULAR_COUNSELING | ASSESSMENT_RETAKE
    trigger_reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="ASSIGNED", nullable=False, index=True
    )  # ASSIGNED | IN_PROGRESS | COMPLETED | ESCALATED | DISMISSED
    action_plan: Mapped[str] = mapped_column(Text, default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    outcome_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Relationships
    student = relationship("User", foreign_keys=[student_user_id], lazy="selectin")
    faculty = relationship("User", foreign_keys=[faculty_user_id], lazy="selectin")

    __table_args__ = (
        Index("ix_interventions_student_status", "student_user_id", "status"),
        Index("ix_interventions_inst_status", "institution_id", "status"),
        Index("ix_interventions_faculty_status", "faculty_user_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Intervention(id={self.id}, student={self.student_user_id}, type='{self.intervention_type}', status='{self.status}')>"


class Notification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """In-app alert and message with strict recipient isolation."""

    __tablename__ = "notifications"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    recipient_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    notification_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # INTERVENTION_ASSIGNED | INTERVENTION_COMPLETED | EVIDENCE_VERIFIED | PROJECT_VERIFIED | REVIEW_DUE | ASSESSMENT_PUBLISHED | ANALYTICS_ALERT
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    link_url: Mapped[str] = mapped_column(String(512), default="", nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    recipient = relationship("User", foreign_keys=[recipient_user_id], lazy="selectin")
    actor = relationship("User", foreign_keys=[actor_user_id], lazy="selectin")

    __table_args__ = (
        Index("ix_notifications_user_read", "recipient_user_id", "is_read", "created_at"),
        Index("ix_notifications_inst_user", "institution_id", "recipient_user_id"),
    )

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, recipient={self.recipient_user_id}, type='{self.notification_type}', is_read={self.is_read})>"


class AnalyticsRollup(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Pre-computed institutional and departmental metrics rollup for < 150ms executive dashboards."""

    __tablename__ = "analytics_rollups"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    rollup_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # INSTITUTIONAL_SUMMARY | DEPARTMENTAL_HEALTH | PASS_RATE_DISTRIBUTION | MASTERY_DISTRIBUTION
    metrics_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )
    period_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_rollups_inst_dept_type", "institution_id", "department_id", "rollup_type"),
        Index("ix_rollups_inst_computed", "institution_id", "computed_at"),
    )

    def __repr__(self) -> str:
        return f"<AnalyticsRollup(id={self.id}, type='{self.rollup_type}', dept={self.department_id})>"
