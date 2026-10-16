"""Dhruva.AI V2 — Student Projects, Portfolios & Placement Domain Models.

Implements the complete Phase 7 schema:
- Project: Student-authored projects with verification lifecycle (DRAFT -> SUBMITTED -> VERIFIED | REJECTED | REVOKED)
- ProjectSkill: Association between projects and institutional skills
- ProjectEvidence: Association between projects and verified learning evidences
- Portfolio: Controlled publication of student portfolios with privacy guards (PRIVATE | INSTITUTION | PUBLIC)
- CareerGoal: Target career roles, industries, target companies, and required competencies
- CareerReadiness: Deterministic, explainable alignment index matching verified skill mastery against career requirements
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


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Student-authored academic, capstone, or research project."""

    __tablename__ = "projects"

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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    project_type: Mapped[str] = mapped_column(
        String(32), default="COURSE_PROJECT", nullable=False
    )  # CAPSTONE | COURSE_PROJECT | RESEARCH | HACKATHON | OPEN_SOURCE
    status: Mapped[str] = mapped_column(
        String(32), default="DRAFT", nullable=False, index=True
    )  # DRAFT | SUBMITTED | VERIFIED | REJECTED | REVOKED
    repository_url: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    deployment_url: Mapped[str] = mapped_column(String(1024), default="", nullable=False)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    contribution_details: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Verification lifecycle
    verified_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_notes: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Revocation lifecycle (if evidence or project integrity is revoked)
    revoked_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[str] = mapped_column(Text, default="", nullable=False)

    # Relationships
    student = relationship("User", foreign_keys=[student_user_id])
    verifier = relationship("User", foreign_keys=[verified_by])
    skills: Mapped[List["ProjectSkill"]] = relationship(
        "ProjectSkill", back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )
    evidences: Mapped[List["ProjectEvidence"]] = relationship(
        "ProjectEvidence", back_populates="project", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_projects_student_inst", "student_user_id", "institution_id"),
        Index("ix_projects_inst_status", "institution_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, title='{self.title}', status='{self.status}')>"


class ProjectSkill(Base, UUIDPrimaryKeyMixin):
    """Association between projects and demonstrated competencies."""

    __tablename__ = "project_skills"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    skill_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    contribution_weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="skills")
    skill = relationship("Skill", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("project_id", "skill_id", name="uq_project_skills_project_skill"),
    )


class ProjectEvidence(Base, UUIDPrimaryKeyMixin):
    """Link between projects and verified learning evidence items."""

    __tablename__ = "project_evidences"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("learning_evidences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    project: Mapped["Project"] = relationship("Project", back_populates="evidences")
    evidence = relationship("LearningEvidence", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("project_id", "evidence_id", name="uq_project_evidences_project_ev"),
    )


class Portfolio(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Controlled publication of student verified profile and portfolio."""

    __tablename__ = "portfolios"

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
    slug: Mapped[str] = mapped_column(String(128), nullable=False)
    headline: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    bio: Mapped[str] = mapped_column(Text, default="", nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(32), default="PRIVATE", nullable=False
    )  # PRIVATE | INSTITUTION | PUBLIC
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    curated_project_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    featured_skill_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    social_links: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    custom_domain: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    student = relationship("User", foreign_keys=[student_user_id])

    __table_args__ = (
        UniqueConstraint("institution_id", "student_user_id", name="uq_portfolios_inst_student"),
        UniqueConstraint("institution_id", "slug", name="uq_portfolios_inst_slug"),
        Index("ix_portfolios_visibility", "institution_id", "visibility", "is_published"),
    )


class CareerGoal(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Student or institution defined career target with required skills."""

    __tablename__ = "career_goals"

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
    target_role: Mapped[str] = mapped_column(String(128), nullable=False)
    target_industry: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    target_companies: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    required_skill_ids: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32), default="ACTIVE", nullable=False
    )  # ACTIVE | ARCHIVED

    student = relationship("User", foreign_keys=[student_user_id])
    readiness_records: Mapped[List["CareerReadiness"]] = relationship(
        "CareerReadiness", back_populates="career_goal", cascade="all, delete-orphan", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_career_goals_student", "student_user_id", "institution_id"),
        Index("ix_career_goals_role", "institution_id", "target_role"),
    )


class CareerReadiness(Base, UUIDPrimaryKeyMixin):
    """Deterministic, explainable career readiness calculation."""

    __tablename__ = "career_readiness"

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
    career_goal_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("career_goals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_role: Mapped[str] = mapped_column(String(128), nullable=False)
    readiness_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    matching_skills_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_required_skills: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_gap_analysis: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    rule_version: Mapped[str] = mapped_column(String(32), default="2026.1", nullable=False)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    calculation_provenance: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    student = relationship("User", foreign_keys=[student_user_id])
    career_goal: Mapped["CareerGoal"] = relationship("CareerGoal", back_populates="readiness_records")

    __table_args__ = (
        Index("ix_readiness_inst_score", "institution_id", "readiness_score"),
        Index("ix_readiness_student_goal", "student_user_id", "career_goal_id"),
    )
