"""Dhruva.AI V2 — Mastery, Skills & Learning Evidence Schemas.

Pydantic schemas for request validation and response serialization.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# CONCEPTS & PREREQUISITES
# =============================================================================
class ConceptCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=64, description="Concept unique code")
    name: str = Field(min_length=2, max_length=255, description="Concept display name")
    description: Optional[str] = Field(default="", description="Detailed concept explanation")
    bloom_level: str = Field(
        default="UNDERSTAND",
        description="REMEMBER | UNDERSTAND | APPLY | ANALYZE | EVALUATE | CREATE",
    )
    department_id: Optional[uuid.UUID] = Field(default=None)
    course_id: Optional[uuid.UUID] = Field(default=None)
    parent_concept_id: Optional[uuid.UUID] = Field(default=None)


class ConceptResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    course_id: Optional[uuid.UUID] = None
    parent_concept_id: Optional[uuid.UUID] = None
    code: str
    name: str
    description: str
    bloom_level: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConceptPrerequisiteCreateRequest(BaseModel):
    concept_id: uuid.UUID
    prerequisite_concept_id: uuid.UUID


class ConceptPrerequisiteResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    concept_id: uuid.UUID
    prerequisite_concept_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# LEARNING OUTCOMES
# =============================================================================
class LearningOutcomeCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=64)
    statement: str = Field(min_length=5)
    bloom_level: str = Field(
        default="APPLY",
        description="REMEMBER | UNDERSTAND | APPLY | ANALYZE | EVALUATE | CREATE",
    )
    course_id: Optional[uuid.UUID] = None
    concept_id: Optional[uuid.UUID] = None
    skill_id: Optional[uuid.UUID] = None


class LearningOutcomeResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    course_id: Optional[uuid.UUID] = None
    code: str
    statement: str
    bloom_level: str
    concept_id: Optional[uuid.UUID] = None
    skill_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# SKILLS
# =============================================================================
class SkillCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=64, description="Skill code e.g. 'SKILL-ALGO-01'")
    name: str = Field(min_length=2, max_length=255, description="Skill title")
    category: str = Field(min_length=2, max_length=64, description="Skill taxonomy category")
    description: Optional[str] = Field(default="", description="Skill criteria and description")


class SkillResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    code: str
    name: str
    category: str
    description: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConceptSkillLinkRequest(BaseModel):
    concept_id: uuid.UUID
    skill_id: uuid.UUID
    weight: float = Field(default=1.0, gt=0.0)


# =============================================================================
# LEARNING EVIDENCE
# =============================================================================
class EvidenceSubmitRequest(BaseModel):
    skill_id: uuid.UUID
    evidence_type: str = Field(
        description="PROJECT_DELIVERABLE | CERTIFICATE | LAB_REPORT | CODE_REPOSITORY | RESEARCH_NOTE"
    )
    title: str = Field(min_length=2, max_length=255)
    description: Optional[str] = Field(default="")
    artifact_url: str = Field(min_length=5, max_length=1024)
    concept_id: Optional[uuid.UUID] = Field(default=None)
    file_size_bytes: Optional[int] = Field(default=None, ge=0)


class EvidenceVerifyRequest(BaseModel):
    is_verified: bool = Field(description="True to approve, False to reject")
    verification_notes: Optional[str] = Field(default="", description="Evaluator feedback")


class EvidenceResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    student_user_id: uuid.UUID
    skill_id: uuid.UUID
    concept_id: Optional[uuid.UUID] = None
    evidence_type: str
    title: str
    description: str
    artifact_url: str
    file_size_bytes: Optional[int] = None
    verification_status: str
    verified_by: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None
    verification_notes: str
    source_assessment_id: Optional[uuid.UUID] = None
    source_submission_id: Optional[uuid.UUID] = None
    source_question_id: Optional[uuid.UUID] = None
    source_result_id: Optional[uuid.UUID] = None
    awarded_score: Optional[float] = None
    max_score: Optional[float] = None
    rule_version: str
    idempotency_key: Optional[str] = None
    is_finalized: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# MASTERY PROFILES
# =============================================================================
class MasteryRecordResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    student_user_id: uuid.UUID
    skill_id: uuid.UUID
    skill: Optional[SkillResponse] = None
    mastery_score: float
    confidence_score: float
    competency_level: str
    assessment_count: int
    evidence_count: int
    decay_factor: float
    rule_version: str
    calculation_provenance: Dict[str, Any]
    is_stale: bool
    last_assessed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# SPACED REVIEWS (SM-2)
# =============================================================================
class ReviewScheduleResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    student_user_id: uuid.UUID
    concept_id: uuid.UUID
    concept: Optional[ConceptResponse] = None
    interval_days: int
    repetition_number: int
    ease_factor: float
    scheduled_for: datetime
    last_reviewed_at: Optional[datetime] = None
    is_completed: bool

    class Config:
        from_attributes = True


class ReviewCompleteRequest(BaseModel):
    quality_rating: int = Field(
        ge=0,
        le=5,
        description="SM-2 recall score from 0 (complete blackout) to 5 (perfect recall)",
    )
