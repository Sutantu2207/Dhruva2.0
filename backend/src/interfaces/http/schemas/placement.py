"""Dhruva.AI V2 — Placement, Projects & Portfolios Schemas.

Pydantic schemas for request validation and response serialization.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# PROJECTS
# =============================================================================
class ProjectCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=255, description="Project title")
    description: Optional[str] = Field(default="", description="Detailed abstract or scope")
    project_type: str = Field(
        default="COURSE_PROJECT",
        description="CAPSTONE | COURSE_PROJECT | RESEARCH | HACKATHON | OPEN_SOURCE",
    )
    repository_url: Optional[str] = Field(default="", description="Source code repository URL")
    deployment_url: Optional[str] = Field(default="", description="Live deployment or demo URL")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    contribution_details: Optional[str] = Field(default="", description="Student specific responsibilities")
    skill_ids: Optional[List[uuid.UUID]] = Field(default_factory=list, description="Demonstrated competencies")


class ProjectUpdateRequest(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    project_type: Optional[str] = None
    repository_url: Optional[str] = None
    deployment_url: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    contribution_details: Optional[str] = None


class ProjectSkillLinkRequest(BaseModel):
    skill_id: uuid.UUID
    weight: float = Field(default=1.0, gt=0.0)


class ProjectEvidenceLinkRequest(BaseModel):
    evidence_id: uuid.UUID


class ProjectVerifyRequest(BaseModel):
    is_verified: bool = Field(description="True to approve, False to reject")
    verification_notes: Optional[str] = Field(default="", description="Faculty review remarks")


class ProjectRevokeRequest(BaseModel):
    revocation_reason: str = Field(min_length=5, description="Detailed justification for revocation")


class ProjectSkillResponse(BaseModel):
    id: uuid.UUID
    skill_id: uuid.UUID
    contribution_weight: float
    skill_code: Optional[str] = None
    skill_name: Optional[str] = None


class ProjectResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    student_user_id: uuid.UUID
    title: str
    description: str
    project_type: str
    status: str
    repository_url: str
    deployment_url: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    contribution_details: str
    verified_by: Optional[uuid.UUID] = None
    verified_at: Optional[datetime] = None
    verification_notes: str
    revoked_by: Optional[uuid.UUID] = None
    revoked_at: Optional[datetime] = None
    revocation_reason: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# PORTFOLIOS
# =============================================================================
class PortfolioUpdateRequest(BaseModel):
    headline: Optional[str] = Field(default=None, max_length=255)
    bio: Optional[str] = None
    visibility: Optional[str] = Field(default=None, description="PRIVATE | INSTITUTION | PUBLIC")
    curated_project_ids: Optional[List[str]] = None
    featured_skill_ids: Optional[List[str]] = None
    social_links: Optional[Dict[str, Any]] = None
    custom_domain: Optional[str] = None


class PortfolioPublishRequest(BaseModel):
    is_published: bool = Field(description="True to publish, False to unpublish")


class PortfolioResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    student_user_id: uuid.UUID
    slug: str
    headline: str
    bio: str
    visibility: str
    is_published: bool
    published_at: Optional[datetime] = None
    curated_project_ids: List[str]
    featured_skill_ids: List[str]
    social_links: Dict[str, Any]
    custom_domain: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# CAREER GOALS & READINESS
# =============================================================================
class CareerGoalRequest(BaseModel):
    target_role: str = Field(min_length=2, max_length=128, description="Target career role")
    target_industry: Optional[str] = Field(default="", max_length=128)
    target_companies: Optional[List[str]] = Field(default_factory=list)
    required_skill_ids: Optional[List[str]] = Field(default_factory=list)


class CareerGoalResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    student_user_id: uuid.UUID
    target_role: str
    target_industry: str
    target_companies: List[str]
    required_skill_ids: List[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CareerReadinessResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    student_user_id: uuid.UUID
    career_goal_id: uuid.UUID
    target_role: str
    readiness_score: float
    matching_skills_count: int
    total_required_skills: int
    target_gap_analysis: Dict[str, Any]
    rule_version: str
    calculated_at: datetime
    calculation_provenance: Dict[str, Any]

    class Config:
        from_attributes = True


# =============================================================================
# TALENT DISCOVERY & PLACEMENT ANALYTICS
# =============================================================================
class TalentCandidateResponse(BaseModel):
    student_id: str
    full_name: str
    email: str
    target_role: str
    readiness_score: float
    matching_skills_count: int
    total_required_skills: int
    portfolio_slug: Optional[str] = None
    portfolio_accessible: bool


class PlacementAnalyticsResponse(BaseModel):
    total_evaluated_students: int
    average_readiness_score: float
    distribution: Dict[str, int]
    top_target_roles: List[Dict[str, Any]]
