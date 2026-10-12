"""Dhruva.AI V2 — Curriculum & Learning Content Schemas.

Pydantic schemas for request validation and response serialization.
Strictly types curriculum versions, syllabus topics, and educational resources.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =========================================================================
# LEARNING RESOURCES
# =========================================================================
class LearningResourceCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255, description="Resource title")
    resource_type: str = Field(
        default="DOCUMENT",
        description="DOCUMENT | SLIDE | CODE | VIDEO | EXTERNAL_LINK | REFERENCE",
    )
    storage_uri: Optional[str] = Field(default=None, max_length=512)
    external_url: Optional[str] = Field(default=None, max_length=512)
    resource_metadata: Dict[str, Any] = Field(default_factory=dict)


class LearningResourceResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    lesson_id: uuid.UUID
    title: str
    resource_type: str
    storage_uri: Optional[str] = None
    external_url: Optional[str] = None
    resource_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# LESSONS / SYLLABUS TOPICS
# =========================================================================
class LessonCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255, description="Lesson / Topic title")
    sequence_order: int = Field(ge=1, description="Sequence order within module")
    content_markdown: Optional[str] = Field(default=None, description="Detailed lecture notes or content in Markdown")
    lesson_type: str = Field(default="THEORY", description="THEORY | LAB | TUTORIAL | WORKSHOP | READING")
    duration_minutes: int = Field(default=60, ge=1, le=1440)


class LessonResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    module_id: uuid.UUID
    sequence_order: int
    title: str
    content_markdown: Optional[str] = None
    lesson_type: str
    duration_minutes: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LessonDetailResponse(LessonResponse):
    learning_resources: List[LearningResourceResponse] = Field(default_factory=list)


# =========================================================================
# MODULES / INSTRUCTIONAL UNITS
# =========================================================================
class ModuleCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255, description="Module title")
    sequence_order: int = Field(ge=1, description="Sequential index within curriculum")
    description: Optional[str] = Field(default=None)
    estimated_hours: float = Field(default=10.0, ge=0.0, le=500.0)
    learning_outcomes: List[str] = Field(default_factory=list)


class ModuleResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    curriculum_id: uuid.UUID
    sequence_order: int
    title: str
    description: Optional[str] = None
    estimated_hours: float
    learning_outcomes: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ModuleDetailResponse(ModuleResponse):
    lessons: List[LessonDetailResponse] = Field(default_factory=list)


# =========================================================================
# CURRICULUMS
# =========================================================================
class CurriculumCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255, description="Curriculum specification title")
    program_id: Optional[uuid.UUID] = Field(default=None, description="Target academic program")
    academic_year_id: Optional[uuid.UUID] = Field(default=None, description="Academic year cycle")
    description: Optional[str] = Field(default=None)
    learning_objectives: List[str] = Field(default_factory=list)


class CurriculumStatusUpdateRequest(BaseModel):
    status: str = Field(description="DRAFT | IN_REVIEW | APPROVED | PUBLISHED | ARCHIVED")


class CurriculumResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    course_id: uuid.UUID
    program_id: Optional[uuid.UUID] = None
    academic_year_id: Optional[uuid.UUID] = None
    title: str
    version: int
    status: str
    description: Optional[str] = None
    learning_objectives: List[str] = Field(default_factory=list)
    approved_by: Optional[uuid.UUID] = None
    approved_at: Optional[datetime] = None
    provenance_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CurriculumDetailResponse(CurriculumResponse):
    modules: List[ModuleDetailResponse] = Field(default_factory=list)
