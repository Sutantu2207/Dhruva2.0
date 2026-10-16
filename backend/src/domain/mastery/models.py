"""Dhruva.AI V2 — Concepts, Skills, Mastery & Learning Evidence Domain Models.

Implements the complete knowledge graph and evidence schema:
- Concept (Academic knowledge graph hierarchy, Bloom's taxonomy levels)
- ConceptPrerequisite (Prerequisite dependency graph between concepts)
- LearningOutcome (Institutional course-level learning outcomes)
- Skill (Core competency definitions and categories)
- ConceptSkill (Weighted mappings between concepts and skills)
- MasteryRecord (Deterministic skill mastery scores, confidence, decay factors, provenance)
- LearningEvidence (Artifact deliverables, assessment evidence, verification workflow, audit trail)
- ReviewSchedule (Spaced repetition retention schedules via deterministic SM-2)
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


class Concept(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Granular unit of academic knowledge within a course or department."""

    __tablename__ = "concepts"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    parent_concept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("concepts.id", ondelete="SET NULL"),
        nullable=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    bloom_level: Mapped[str] = mapped_column(
        String(32), default="UNDERSTAND", nullable=False
    )  # REMEMBER | UNDERSTAND | APPLY | ANALYZE | EVALUATE | CREATE

    # Relationships
    parent_concept = relationship("Concept", remote_side="Concept.id", backref="sub_concepts")
    skills: Mapped[List["ConceptSkill"]] = relationship(
        "ConceptSkill", back_populates="concept", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_concepts_institution_code"),
        Index("ix_concepts_inst_course", "institution_id", "course_id"),
        Index("ix_concepts_inst_dept", "institution_id", "department_id"),
    )


class ConceptPrerequisite(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Directed dependency requirement between concepts."""

    __tablename__ = "concept_prerequisites"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concept_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prerequisite_concept_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    concept: Mapped["Concept"] = relationship("Concept", foreign_keys=[concept_id])
    prerequisite_concept: Mapped["Concept"] = relationship(
        "Concept", foreign_keys=[prerequisite_concept_id]
    )

    __table_args__ = (
        UniqueConstraint(
            "concept_id",
            "prerequisite_concept_id",
            name="uq_concept_prerequisites_pair",
        ),
        Index("ix_concept_prereq_inst", "institution_id", "concept_id"),
    )


class LearningOutcome(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Accredited learning outcome mapped to courses, concepts, and skills."""

    __tablename__ = "learning_outcomes"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    bloom_level: Mapped[str] = mapped_column(
        String(32), default="APPLY", nullable=False
    )  # REMEMBER | UNDERSTAND | APPLY | ANALYZE | EVALUATE | CREATE
    concept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("concepts.id", ondelete="SET NULL"),
        nullable=True,
    )
    skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("skills.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    concept: Mapped[Optional["Concept"]] = relationship("Concept")
    skill: Mapped[Optional["Skill"]] = relationship("Skill")

    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_learning_outcomes_inst_code"),
        Index("ix_learning_outcomes_inst_course", "institution_id", "course_id"),
    )


class Skill(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Institutional competency or technical ability."""

    __tablename__ = "skills"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Relationships
    concepts: Mapped[List["ConceptSkill"]] = relationship(
        "ConceptSkill", back_populates="skill", cascade="all, delete-orphan"
    )
    mastery_records: Mapped[List["MasteryRecord"]] = relationship(
        "MasteryRecord", back_populates="skill", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_skills_institution_code"),
        Index("ix_skills_inst_cat", "institution_id", "category"),
    )


class ConceptSkill(Base):
    """Weighted association between concepts and corresponding skills."""

    __tablename__ = "concept_skills"

    concept_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        primary_key=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        primary_key=True,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Relationships
    concept: Mapped["Concept"] = relationship("Concept", back_populates="skills")
    skill: Mapped["Skill"] = relationship("Skill", back_populates="concepts")


class MasteryRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authoritative student mastery level for a specific skill."""

    __tablename__ = "mastery_records"

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
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mastery_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # 0.0 to 1.0
    confidence_score: Mapped[float] = mapped_column(
        Float, default=0.0, nullable=False
    )  # 0.0 to 1.0
    competency_level: Mapped[str] = mapped_column(
        String(32), default="INSUFFICIENT_EVIDENCE", nullable=False
    )  # INSUFFICIENT_EVIDENCE | NOVICE | DEVELOPING | COMPETENT | PROFICIENT | MASTERY
    assessment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    decay_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    rule_version: Mapped[str] = mapped_column(String(32), default="2026.1", nullable=False)
    calculation_provenance: Mapped[Dict[str, Any]] = mapped_column(
        JSON, default=dict, nullable=False
    )
    is_stale: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_assessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill", back_populates="mastery_records")

    __table_args__ = (
        UniqueConstraint(
            "institution_id",
            "student_user_id",
            "skill_id",
            name="uq_mastery_inst_student_skill",
        ),
        Index("ix_mastery_student_skill", "student_user_id", "skill_id", "institution_id"),
        Index("ix_mastery_inst_score", "institution_id", "mastery_score"),
    )


class LearningEvidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Artifact or deliverable proving student competency."""

    __tablename__ = "learning_evidences"

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
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concept_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("concepts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    evidence_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # PROJECT_DELIVERABLE | CERTIFICATE | LAB_REPORT | CODE_REPOSITORY | RESEARCH_NOTE | ASSESSMENT_RESULT
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    artifact_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(32), default="PENDING", nullable=False
    )  # PENDING | VERIFIED | REJECTED
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    verification_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Provenance tracking from assessment source
    source_assessment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("assessments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_submission_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("submissions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_question_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_result_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("results.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    awarded_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    rule_version: Mapped[str] = mapped_column(String(32), default="2026.1", nullable=False)
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, unique=True, index=True
    )
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    skill: Mapped["Skill"] = relationship("Skill")
    concept: Mapped[Optional["Concept"]] = relationship("Concept")

    __table_args__ = (
        Index("ix_evidence_inst_student", "institution_id", "student_user_id"),
        Index("ix_evidence_inst_status", "institution_id", "verification_status"),
        Index("ix_evidence_source_result", "source_result_id", "source_question_id"),
    )


class ReviewSchedule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Spaced repetition schedule calculated via SuperMemo SM-2 algorithm."""

    __tablename__ = "review_schedules"

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
    concept_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interval_days: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    repetition_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5, nullable=False)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    concept: Mapped["Concept"] = relationship("Concept")

    __table_args__ = (
        Index(
            "ix_review_sched_student",
            "student_user_id",
            "scheduled_for",
            "is_completed",
        ),
    )
