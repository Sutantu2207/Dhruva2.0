"""Dhruva.AI V2 — Analytics, Interventions & Notifications Pydantic Schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


# ==========================================
# INTERVENTION SCHEMAS
# ==========================================

class InterventionCreateRequest(BaseModel):
    student_user_id: uuid.UUID
    faculty_user_id: Optional[uuid.UUID] = None
    intervention_type: str = Field(..., min_length=2, max_length=64)
    trigger_reason: str = Field(..., min_length=5, max_length=1000)
    action_plan: str = Field(default="", max_length=2000)
    notes: str = Field(default="", max_length=2000)
    due_date: Optional[datetime] = None


class InterventionUpdateRequest(BaseModel):
    status: Optional[str] = None
    action_plan: Optional[str] = Field(None, max_length=2000)
    outcome_notes: Optional[str] = Field(None, max_length=2000)


class InterventionResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    student_user_id: uuid.UUID
    faculty_user_id: Optional[uuid.UUID] = None
    intervention_type: str
    trigger_reason: str
    status: str
    action_plan: str
    notes: str
    assigned_at: datetime
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outcome_notes: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==========================================
# NOTIFICATION SCHEMAS
# ==========================================

class NotificationResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    recipient_user_id: uuid.UUID
    actor_user_id: Optional[uuid.UUID] = None
    notification_type: str
    title: str
    message: str
    link_url: str = ""
    is_read: bool
    read_at: Optional[datetime] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationBatchReadResponse(BaseModel):
    updated_count: int


# ==========================================
# EARLY WARNING & ANALYTICS SCHEMAS
# ==========================================

class AtRiskStudentResponse(BaseModel):
    student_id: str
    full_name: str
    email: str
    roll_number: str
    risk_level: str
    detected_rules: List[Dict[str, Any]] = Field(default_factory=list)
    recommended_intervention_type: str
    trigger_reason: str
    metrics_summary: Dict[str, Any] = Field(default_factory=dict)


class AnalyticsRollupResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    department_id: Optional[uuid.UUID] = None
    rollup_type: str
    metrics_payload: Dict[str, Any]
    computed_at: datetime
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None

    class Config:
        from_attributes = True
