"""Dhruva.AI V2 — Assessment, Question Bank & Deterministic Grading Domain Models.

Implements the complete assessment schema from Master Architecture Section 3.3:
- QuestionBank & Question (MCQ, Multi-select, Numerical, Structured-text)
- Assessment & AssessmentQuestion (Configuration, schedule, mark allocation)
- AssessmentSubmission (Secure student attempts, timestamps)
- AssessmentResult (Itemized deterministic breakdown, percentage, passing flags)
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


class QuestionBank(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Institutional question repository scoped by department and course."""

    __tablename__ = "question_banks"

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
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="question_bank",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_question_banks_inst_course", "institution_id", "course_id"),
        Index("ix_question_banks_inst_dept", "institution_id", "department_id"),
    )

    def __repr__(self) -> str:
        return f"<QuestionBank(id={self.id}, title='{self.title}')>"


class Question(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authored assessment question with strict deterministic answer key."""

    __tablename__ = "questions"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_bank_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("question_banks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        index=True,
    )  # MCQ | MULTI_SELECT | NUMERICAL | STRUCTURED_TEXT
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    answer_key: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    points: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(16), default="MEDIUM", nullable=False)
    explanation: Mapped[str] = mapped_column(Text, default="", nullable=False)

    concept_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    skill_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid(as_uuid=True), nullable=True, index=True)
    provenance_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("provenance_records.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    question_bank: Mapped["QuestionBank"] = relationship("QuestionBank", back_populates="questions", lazy="selectin")
    assessment_links: Mapped[List["AssessmentQuestion"]] = relationship(
        "AssessmentQuestion",
        back_populates="question",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_questions_bank_type", "question_bank_id", "question_type"),
        Index("ix_questions_inst_bank", "institution_id", "question_bank_id"),
    )

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, type='{self.question_type}', points={self.points})>"


class Assessment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Scheduled assessment tied to a specific course offering."""

    __tablename__ = "assessments"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_offering_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("course_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    instructions: Mapped[str] = mapped_column(Text, default="", nullable=False)
    assessment_type: Mapped[str] = mapped_column(
        String(32),
        default="QUIZ",
        nullable=False,
    )  # QUIZ | ASSIGNMENT | MIDTERM | FINAL_EXAM
    status: Mapped[str] = mapped_column(
        String(32),
        default="DRAFT",
        nullable=False,
        index=True,
    )  # DRAFT | PUBLISHED | CLOSED | ARCHIVED
    publish_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    passing_percentage: Mapped[float] = mapped_column(Float, default=40.0, nullable=False)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    questions: Mapped[List["AssessmentQuestion"]] = relationship(
        "AssessmentQuestion",
        back_populates="assessment",
        cascade="all, delete-orphan",
        order_by="AssessmentQuestion.sort_order",
        lazy="selectin",
    )
    submissions: Mapped[List["AssessmentSubmission"]] = relationship(
        "AssessmentSubmission",
        back_populates="assessment",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_assessments_inst_offering", "institution_id", "course_offering_id"),
        Index("ix_assessments_offering_dates", "course_offering_id", "publish_at", "due_at"),
    )

    def __repr__(self) -> str:
        return f"<Assessment(id={self.id}, title='{self.title}', status='{self.status}')>"


class AssessmentQuestion(Base, UUIDPrimaryKeyMixin):
    """Many-to-many link ordering and allocating points to questions in an assessment."""

    __tablename__ = "assessment_questions"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    points: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="questions", lazy="selectin")
    question: Mapped["Question"] = relationship("Question", back_populates="assessment_links", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("assessment_id", "question_id", name="uq_assessment_question"),
        Index("ix_assessment_questions_order", "assessment_id", "sort_order"),
    )

    def __repr__(self) -> str:
        return f"<AssessmentQuestion(assessment={self.assessment_id}, question={self.question_id}, points={self.points})>"


class AssessmentSubmission(Base, UUIDPrimaryKeyMixin):
    """Student submission attempt holding answers payload."""

    __tablename__ = "submissions"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    answers_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        default="SUBMITTED",
        nullable=False,
        index=True,
    )  # IN_PROGRESS | SUBMITTED | GRADED | LATE_REJECTED
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    assessment: Mapped["Assessment"] = relationship("Assessment", back_populates="submissions", lazy="selectin")
    result: Mapped[Optional["AssessmentResult"]] = relationship(
        "AssessmentResult",
        back_populates="submission",
        uselist=False,
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint("assessment_id", "student_user_id", "attempt_number", name="uq_submission_attempt"),
        Index("ix_submissions_inst_student", "institution_id", "student_user_id"),
        Index("ix_submissions_assessment_status", "assessment_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<AssessmentSubmission(id={self.id}, student={self.student_user_id}, attempt={self.attempt_number})>"


class AssessmentResult(Base, UUIDPrimaryKeyMixin):
    """Deterministic grade output containing itemized breakdown and score calculations."""

    __tablename__ = "results"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    submission_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("submissions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    raw_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    total_points: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    percentage: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    grade_letter: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    is_passed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    itemized_breakdown: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list, nullable=False)
    is_finalized: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    graded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    graded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    submission: Mapped["AssessmentSubmission"] = relationship("AssessmentSubmission", back_populates="result", lazy="selectin")

    __table_args__ = (
        Index("ix_results_inst_submission", "institution_id", "submission_id"),
    )

    def __repr__(self) -> str:
        return f"<AssessmentResult(id={self.id}, score={self.raw_score}/{self.total_points}, {self.percentage}%)>"
