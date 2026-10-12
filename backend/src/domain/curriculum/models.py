"""Dhruva.AI V2 — Curriculum, Syllabus & Learning Content Models.

Defines the normalized curriculum domain matching Master Architecture Section 3.2:
- Curriculum: Versioned course curriculum specification with learning objectives and approval status.
- Module: Sequence-ordered instructional unit within a curriculum.
- Lesson: Sequence-ordered instructional topic / lesson / syllabus unit within a module.
- LearningResource: Educational material metadata and media links attached to lessons.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
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


class Curriculum(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Versioned Course Curriculum Entity."""

    __tablename__ = "curriculums"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("programs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    academic_year_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="DRAFT", nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    learning_objectives: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    provenance_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    modules: Mapped[List["Module"]] = relationship(
        "Module",
        back_populates="curriculum",
        cascade="all, delete-orphan",
        order_by="Module.sequence_order",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("course_id", "version", name="uq_curriculum_course_version"),
        Index("ix_curriculums_inst_course", "institution_id", "course_id"),
        Index("ix_curriculums_status", "institution_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Curriculum(id={self.id}, course_id={self.course_id}, v={self.version}, status={self.status})>"


class Module(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Instructional Unit / Module within a Curriculum."""

    __tablename__ = "modules"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    curriculum_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("curriculums.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_hours: Mapped[float] = mapped_column(Float, default=10.0, nullable=False)
    learning_outcomes: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)

    # Relationships
    curriculum: Mapped["Curriculum"] = relationship("Curriculum", back_populates="modules", lazy="selectin")
    lessons: Mapped[List["Lesson"]] = relationship(
        "Lesson",
        back_populates="module",
        cascade="all, delete-orphan",
        order_by="Lesson.sequence_order",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("curriculum_id", "sequence_order", name="uq_module_curriculum_seq"),
        Index("ix_modules_curriculum_seq", "curriculum_id", "sequence_order"),
    )

    def __repr__(self) -> str:
        return f"<Module(id={self.id}, seq={self.sequence_order}, title={self.title})>"


class Lesson(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Syllabus Topic / Lesson within an Instructional Module."""

    __tablename__ = "lessons"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    module_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lesson_type: Mapped[str] = mapped_column(String(32), default="THEORY", nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    # Relationships
    module: Mapped["Module"] = relationship("Module", back_populates="lessons", lazy="selectin")
    learning_resources: Mapped[List["LearningResource"]] = relationship(
        "LearningResource",
        back_populates="lesson",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("module_id", "sequence_order", name="uq_lesson_module_seq"),
        Index("ix_lessons_module_seq", "module_id", "sequence_order"),
    )

    def __repr__(self) -> str:
        return f"<Lesson(id={self.id}, seq={self.sequence_order}, title={self.title}, type={self.lesson_type})>"


class LearningResource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Educational Material Attached to a Lesson."""

    __tablename__ = "learning_resources"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lesson_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("lessons.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(32), default="DOCUMENT", nullable=False)
    storage_uri: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    external_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    resource_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    provenance_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True)

    # Relationships
    lesson: Mapped["Lesson"] = relationship("Lesson", back_populates="learning_resources", lazy="selectin")

    __table_args__ = (
        Index("ix_resources_lesson_id", "lesson_id"),
        Index("ix_resources_inst", "institution_id"),
    )

    def __repr__(self) -> str:
        return f"<LearningResource(id={self.id}, title={self.title}, type={self.resource_type})>"
