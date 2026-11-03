"""Dhruva.AI V2 — College API Request & Response Schemas."""

import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CollegeResponse(BaseModel):
    """Accredited college public details."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: Optional[str] = None
    institution_type: str
    affiliated_university: Optional[str] = None
    location: str
    district: str
    state: str
    website: Optional[str] = None
    accreditation: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class CollegeCreateRequest(BaseModel):
    """Admin payload to add an institution."""
    name: str = Field(..., min_length=2, max_length=255)
    code: Optional[str] = Field(None, max_length=32)
    institution_type: str = Field(..., max_length=64)
    affiliated_university: Optional[str] = Field(None, max_length=255)
    location: str = Field(..., min_length=2, max_length=255)
    district: str = Field(default="Coimbatore", max_length=64)
    state: str = Field(default="Tamil Nadu", max_length=64)
    website: Optional[str] = Field(None, max_length=255)
    accreditation: Optional[str] = Field(None, max_length=255)
    status: str = Field(default="ACTIVE", max_length=32)


class CollegeUpdateRequest(BaseModel):
    """Admin payload to update an existing institution."""
    name: Optional[str] = None
    code: Optional[str] = None
    institution_type: Optional[str] = None
    affiliated_university: Optional[str] = None
    location: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    website: Optional[str] = None
    accreditation: Optional[str] = None
    status: Optional[str] = None


class CollegeSubmitRequest(BaseModel):
    """User payload to request addition of an unlisted college."""
    college_name: str = Field(..., min_length=2, max_length=255)
    requester_name: str = Field(..., min_length=2, max_length=128)
    requester_email: EmailStr
    institution_type: Optional[str] = Field(None, max_length=64)
    location: Optional[str] = Field(None, max_length=255)


class CollegeRequestResponse(BaseModel):
    """User-submitted college addition request."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    requester_name: str
    requester_email: str
    college_name: str
    institution_type: Optional[str] = None
    location: Optional[str] = None
    status: str
    admin_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CollegeRequestAction(BaseModel):
    """Admin approval or rejection action notes."""
    admin_notes: Optional[str] = None


class CollegeAnalyticsItem(BaseModel):
    """Aggregated statistics for a specific institution."""
    college_id: str
    college_name: str
    college_code: Optional[str] = None
    institution_type: str
    location: str
    district: str
    enrolled_students: int
    career_readiness_avg: float
    assessment_completion_rate: float


class UpdateUserCollegeRequest(BaseModel):
    """Student profile update payload for selected college."""
    college_id: uuid.UUID

