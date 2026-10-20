"""Dhruva.AI V2 — Guardrailed AI Gateway Domain Models.

Implements Phase 9 persistent state:
- AIConversation: Session tracking for student tutor and faculty drafting co-pilots.
- AIMessage: Grounded messages with sanitization history, provenance citations, and telemetry.
- AIAuditLog: Immutable audit log recording prompt hash, PII detections, prompt injection verdicts, and token costs.
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


class AIConversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Multi-tenant AI conversation session."""

    __tablename__ = "ai_conversations"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    context_type: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # STUDENT_TUTOR | FACULTY_DRAFT | FEEDBACK_SUMMARY
    context_id: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True, index=True
    )  # e.g. course_id, lesson_id, or question_bank_id
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False
    )  # ACTIVE | ARCHIVED

    # Relationships
    messages: Mapped[List["AIMessage"]] = relationship(
        "AIMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AIMessage.created_at",
    )

    __table_args__ = (
        Index("ix_ai_conv_inst_user", "institution_id", "user_id"),
        Index("ix_ai_conv_inst_context", "institution_id", "context_type", "context_id"),
    )

    def __repr__(self) -> str:
        return f"<AIConversation(id={self.id}, user_id={self.user_id}, type={self.context_type})>"


class AIMessage(Base, UUIDPrimaryKeyMixin):
    """Single message entry in an AI conversation with strict citation metadata."""

    __tablename__ = "ai_messages"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("ai_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_role: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # USER | ASSISTANT | SYSTEM
    raw_content: Mapped[str] = mapped_column(Text, nullable=False)
    sanitized_content: Mapped[str] = mapped_column(Text, nullable=False)
    citations_json: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON, default=list, nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(64), default="dhruva-grounded-v2", nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    # Relationships
    conversation: Mapped["AIConversation"] = relationship("AIConversation", back_populates="messages")

    __table_args__ = (
        Index("ix_ai_msg_conv_created", "conversation_id", "created_at"),
        Index("ix_ai_msg_inst_conv", "institution_id", "conversation_id"),
    )

    def __repr__(self) -> str:
        return f"<AIMessage(id={self.id}, role={self.sender_role}, model={self.model_name})>"


class AIAuditLog(Base, UUIDPrimaryKeyMixin):
    """Immutable audit entry tracking AI safety, prompt injection verdicts, and PII redacting."""

    __tablename__ = "ai_audit_logs"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # TUTOR_QUERY | QUESTION_DRAFT | FEEDBACK_SUMMARY | PROMPT_INJECTION_BLOCKED
    prompt_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    pii_detected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    safety_verdict: Mapped[str] = mapped_column(
        String(32), default="PASS", nullable=False, index=True
    )  # PASS | FLAGGED | BLOCKED
    tokens_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_estimate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    __table_args__ = (
        Index("ix_ai_audit_inst_user_created", "institution_id", "user_id", "created_at"),
        Index("ix_ai_audit_verdict", "institution_id", "safety_verdict"),
    )

    def __repr__(self) -> str:
        return f"<AIAuditLog(id={self.id}, action={self.action}, verdict={self.safety_verdict})>"
