"""Dhruva.AI V2 — Assessment & Grading API Schemas.

Pydantic schemas for request validation and response serialization.
Strictly separates privileged author/faculty views from student views to guarantee
ZERO ANSWER KEY LEAKAGE.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =========================================================================
# QUESTION BANKS
# =========================================================================
class QuestionBankCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255, description="Question bank title")
    description: Optional[str] = Field(default="", description="Optional description")
    course_id: Optional[uuid.UUID] = Field(default=None, description="Linked course ID")
    department_id: Optional[uuid.UUID] = Field(default=None, description="Linked department ID")


class QuestionBankResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    course_id: Optional[uuid.UUID] = None
    title: str
    description: str
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# QUESTIONS
# =========================================================================
class QuestionOption(BaseModel):
    id: str = Field(description="Unique option identifier e.g. 'opt_1'")
    text: str = Field(description="Option display text")


class QuestionCreateRequest(BaseModel):
    question_type: str = Field(
        description="MCQ | MULTI_SELECT | NUMERICAL | STRUCTURED_TEXT"
    )
    prompt_text: str = Field(min_length=3, description="Question prompt / markdown")
    answer_key: Dict[str, Any] = Field(
        description="Deterministic answer key (e.g. {'correct_option_id': 'opt_1'})"
    )
    options: Optional[List[Dict[str, Any]]] = Field(
        default_factory=list, description="List of options for MCQ / Multi-select"
    )
    points: float = Field(default=1.0, gt=0, description="Allocated marks (> 0)")
    difficulty: str = Field(default="MEDIUM", description="EASY | MEDIUM | HARD")
    explanation: Optional[str] = Field(default="", description="Educational rationale")
    concept_id: Optional[uuid.UUID] = Field(default=None)
    skill_id: Optional[uuid.UUID] = Field(default=None)


class QuestionAdminResponse(BaseModel):
    """Privileged response containing full answer key for authors and faculty."""

    id: uuid.UUID
    institution_id: uuid.UUID
    question_bank_id: uuid.UUID
    question_type: str
    prompt_text: str
    options: List[Dict[str, Any]]
    answer_key: Dict[str, Any]
    points: float
    difficulty: str
    explanation: str
    concept_id: Optional[uuid.UUID] = None
    skill_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuestionStudentResponse(BaseModel):
    """Sanitized student response with ZERO answer key or privileged explanations."""

    id: uuid.UUID
    question_type: str
    prompt_text: str
    options: List[Dict[str, Any]]
    points: float
    difficulty: str

    class Config:
        from_attributes = True


# =========================================================================
# ASSESSMENTS
# =========================================================================
class AssessmentCreateRequest(BaseModel):
    course_offering_id: uuid.UUID = Field(description="Target course offering ID")
    title: str = Field(min_length=2, max_length=255)
    instructions: Optional[str] = Field(default="", description="Exam guidelines")
    assessment_type: str = Field(default="QUIZ", description="QUIZ | ASSIGNMENT | MIDTERM | FINAL_EXAM")
    publish_at: datetime = Field(description="UTC timestamp when assessment opens")
    due_at: datetime = Field(description="UTC timestamp submission cutoff deadline")
    duration_minutes: Optional[int] = Field(default=None, gt=0, description="Timer in minutes")
    passing_percentage: float = Field(default=40.0, ge=0.0, le=100.0)
    max_attempts: int = Field(default=1, ge=1)


class AssessmentQuestionAddRequest(BaseModel):
    question_id: uuid.UUID = Field(description="ID of question from question bank")
    points: Optional[float] = Field(default=None, gt=0, description="Override points for this assessment")
    sort_order: Optional[int] = Field(default=None, ge=0)


class AssessmentQuestionResponse(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    points: float
    sort_order: int
    question: QuestionAdminResponse

    class Config:
        from_attributes = True


class AssessmentStudentQuestionResponse(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    points: float
    sort_order: int
    question: QuestionStudentResponse

    class Config:
        from_attributes = True


class AssessmentResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    course_offering_id: uuid.UUID
    title: str
    instructions: str
    assessment_type: str
    status: str
    publish_at: datetime
    due_at: datetime
    duration_minutes: Optional[int] = None
    total_points: float
    passing_percentage: float
    max_attempts: int
    created_by: Optional[uuid.UUID] = None
    questions: List[AssessmentQuestionResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AssessmentStudentDetailResponse(BaseModel):
    """Sanitized student assessment view during test taking."""

    id: uuid.UUID
    course_offering_id: uuid.UUID
    title: str
    instructions: str
    assessment_type: str
    status: str
    publish_at: datetime
    due_at: datetime
    duration_minutes: Optional[int] = None
    total_points: float
    passing_percentage: float
    max_attempts: int
    questions: List[AssessmentStudentQuestionResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# =========================================================================
# SUBMISSIONS & RESULTS
# =========================================================================
class SubmissionCreateRequest(BaseModel):
    answers_payload: Dict[str, Any] = Field(
        description="Key-value mapping of question_id (string) to submitted answer value"
    )


class AssessmentResultResponse(BaseModel):
    id: uuid.UUID
    submission_id: uuid.UUID
    raw_score: float
    total_points: float
    percentage: float
    grade_letter: Optional[str] = None
    is_passed: bool
    itemized_breakdown: List[Dict[str, Any]]
    is_finalized: bool
    graded_by: Optional[uuid.UUID] = None
    graded_at: datetime

    class Config:
        from_attributes = True


class SubmissionResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    assessment_id: uuid.UUID
    student_user_id: uuid.UUID
    attempt_number: int
    answers_payload: Dict[str, Any]
    status: str
    started_at: datetime
    submitted_at: Optional[datetime] = None
    result: Optional[AssessmentResultResponse] = None

    class Config:
        from_attributes = True


class ManualGradeRequest(BaseModel):
    question_id: uuid.UUID = Field(description="Target subjective question ID")
    awarded_points: float = Field(ge=0.0, description="Marks awarded by evaluator")
    feedback: Optional[str] = Field(default="", description="Evaluator feedback")
