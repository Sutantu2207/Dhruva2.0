"""Dhruva.AI V2 — Guardrailed AI Gateway Pydantic Schemas."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==========================================
# 1. TUTOR CHAT SCHEMAS
# ==========================================

class TutorChatRequest(BaseModel):
    course_id: uuid.UUID
    message: str = Field(..., min_length=2, max_length=2000)
    conversation_id: Optional[uuid.UUID] = None


class CitationItem(BaseModel):
    citation_id: str
    source_type: str
    entity_id: str
    title: str
    course_code: str
    provenance: str


class TutorChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message_id: uuid.UUID
    course_id: uuid.UUID
    course_code: str
    role: str
    content: str
    citations: List[CitationItem] = Field(default_factory=list)
    model_name: str
    pii_detected_count: int
    latency_ms: int
    is_refusal: bool
    created_at: datetime


# ==========================================
# 2. QUESTION DRAFTING SCHEMAS
# ==========================================

class QuestionDraftRequest(BaseModel):
    course_id: uuid.UUID
    topic_or_concept: str = Field(..., min_length=2, max_length=128)
    difficulty: str = Field(default="MEDIUM", pattern="^(EASY|MEDIUM|HARD)$")
    num_questions: int = Field(default=3, ge=1, le=10)


class DraftQuestionOption(BaseModel):
    text: str
    is_correct: bool


class DraftQuestionItem(BaseModel):
    draft_id: str
    title: str
    question_text: str
    question_type: str
    difficulty: str
    bloom_level: str
    points: float
    options: List[DraftQuestionOption]
    explanation: str


class QuestionDraftResponse(BaseModel):
    course_id: uuid.UUID
    course_code: str
    topic: str
    difficulty: str
    draft_questions: List[DraftQuestionItem]
    total_generated: int


# ==========================================
# 3. FEEDBACK SUMMARY SCHEMAS
# ==========================================

class FeedbackSummaryRequest(BaseModel):
    course_id: uuid.UUID
    feedback_items: List[str] = Field(..., min_length=1)


class FeedbackSummaryResponse(BaseModel):
    course_id: uuid.UUID
    course_code: str
    total_submissions: int
    pii_sanitized_count: int
    summary: str
    strengths: List[str]
    areas_for_improvement: List[str]
    actionable_recommendations: List[str]


# ==========================================
# 4. CONVERSATION & AUDIT LOG SCHEMAS
# ==========================================

class AIConversationResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    user_id: uuid.UUID
    context_type: str
    context_id: Optional[str] = None
    title: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AIAuditLogResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    user_id: uuid.UUID
    action: str
    prompt_hash: str
    pii_detected_count: int
    safety_verdict: str
    tokens_used: int
    cost_estimate: float
    metadata_json: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True


class AIMessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_role: str
    raw_content: str
    sanitized_content: str
    citations_json: List[Dict[str, Any]] = Field(default_factory=list)
    model_name: str
    token_count: int
    latency_ms: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProviderConfigItem(BaseModel):
    configured: bool
    model: str
    status: Optional[str] = "UNKNOWN"
    verdict: Optional[str] = None
    detail: Optional[str] = None
    remediation: Optional[str] = None


class AIProviderStatusResponse(BaseModel):
    active_provider: str
    active_model: str
    status: str
    latency_ms: float
    diagnostic_verdict: Optional[str] = None
    remediation: Optional[str] = None
    configured_providers: Dict[str, ProviderConfigItem]

