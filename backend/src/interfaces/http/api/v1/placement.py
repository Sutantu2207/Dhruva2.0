"""Dhruva.AI V2 — Student Projects, Portfolios & Placement API Endpoints.

Prefix: /institutions/{institution_slug}/...
Enforces:
- Strict multi-tenant isolation.
- RBAC permissions (students author projects and portfolios; staff verify and revoke; placement officers discover talent).
- Deterministic career readiness calculation.
"""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.placement.placement_service import PlacementService
from src.domain.identity.models import Institution, User
from src.domain.identity.roles import SystemRole
from src.infrastructure.persistence.postgres.database import get_db_session
from src.interfaces.http.dependencies import (
    build_response,
    get_current_tenant,
    get_current_user,
    require_roles,
)
from src.interfaces.http.schemas.envelope import ApiResponse, PaginationMeta
from src.interfaces.http.schemas.placement import (
    CareerGoalRequest,
    CareerGoalResponse,
    CareerReadinessResponse,
    PlacementAnalyticsResponse,
    PortfolioPublishRequest,
    PortfolioResponse,
    PortfolioUpdateRequest,
    ProjectCreateRequest,
    ProjectEvidenceLinkRequest,
    ProjectResponse,
    ProjectRevokeRequest,
    ProjectSkillLinkRequest,
    ProjectUpdateRequest,
    ProjectVerifyRequest,
    TalentCandidateResponse,
)

router = APIRouter(prefix="/institutions/{institution_slug}", tags=["Projects, Portfolios & Placement"])


# =============================================================================
# 1. STUDENT PROJECT STUDIO
# =============================================================================
@router.post(
    "/projects",
    response_model=ApiResponse[ProjectResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Project Deliverable",
)
async def create_project(
    request: Request,
    payload: ProjectCreateRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ProjectResponse]:
    service = PlacementService(session)
    project = await service.create_project(
        institution_id=tenant.id,
        student_user_id=user.id,
        title=payload.title,
        description=payload.description or "",
        project_type=payload.project_type,
        repository_url=payload.repository_url or "",
        deployment_url=payload.deployment_url or "",
        start_date=payload.start_date,
        end_date=payload.end_date,
        contribution_details=payload.contribution_details or "",
        skill_ids=payload.skill_ids,
    )
    return build_response(data=ProjectResponse.model_validate(project), request=request)


@router.get(
    "/projects",
    response_model=ApiResponse[List[ProjectResponse]],
    summary="List Projects",
)
async def list_projects(
    request: Request,
    student_id: Optional[uuid.UUID] = Query(default=None),
    status_filter: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[ProjectResponse]]:
    service = PlacementService(session)
    target_student_id = student_id or user.id
    offset = (page - 1) * page_size
    projects = await service.list_student_projects(
        institution_id=tenant.id,
        student_user_id=target_student_id,
        status=status_filter,
        limit=page_size,
        offset=offset,
    )
    data = [ProjectResponse.model_validate(p) for p in projects]
    return build_response(
        data=data,
        request=request,
        pagination=PaginationMeta(page=page, page_size=page_size, total_records=len(data)),
    )


@router.get(
    "/projects/{project_id}",
    response_model=ApiResponse[ProjectResponse],
    summary="Get Project by ID",
)
async def get_project(
    request: Request,
    project_id: uuid.UUID,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ProjectResponse]:
    service = PlacementService(session)
    project = await service.get_project(tenant.id, project_id)
    return build_response(data=ProjectResponse.model_validate(project), request=request)


@router.put(
    "/projects/{project_id}",
    response_model=ApiResponse[ProjectResponse],
    summary="Update Project",
)
async def update_project(
    request: Request,
    project_id: uuid.UUID,
    payload: ProjectUpdateRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ProjectResponse]:
    service = PlacementService(session)
    project = await service.update_project(
        institution_id=tenant.id,
        project_id=project_id,
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        project_type=payload.project_type,
        repository_url=payload.repository_url,
        deployment_url=payload.deployment_url,
        start_date=payload.start_date,
        end_date=payload.end_date,
        contribution_details=payload.contribution_details,
    )
    return build_response(data=ProjectResponse.model_validate(project), request=request)


@router.post(
    "/projects/{project_id}/submit",
    response_model=ApiResponse[ProjectResponse],
    summary="Submit Project for Faculty Review",
)
async def submit_project(
    request: Request,
    project_id: uuid.UUID,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ProjectResponse]:
    service = PlacementService(session)
    project = await service.submit_project(tenant.id, project_id, user.id)
    return build_response(data=ProjectResponse.model_validate(project), request=request)


@router.post(
    "/projects/{project_id}/link-skill",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Link Skill to Project",
)
async def link_skill_to_project(
    request: Request,
    project_id: uuid.UUID,
    payload: ProjectSkillLinkRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[Dict[str, Any]]:
    service = PlacementService(session)
    ps = await service.link_skill_to_project(
        institution_id=tenant.id,
        project_id=project_id,
        skill_id=payload.skill_id,
        user_id=user.id,
        weight=payload.weight,
    )
    return build_response(
        data={"project_id": str(ps.project_id), "skill_id": str(ps.skill_id), "weight": ps.contribution_weight},
        request=request,
    )


@router.post(
    "/projects/{project_id}/link-evidence",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Link Evidence Artifact to Project",
)
async def link_evidence_to_project(
    request: Request,
    project_id: uuid.UUID,
    payload: ProjectEvidenceLinkRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[Dict[str, Any]]:
    service = PlacementService(session)
    pe = await service.link_evidence_to_project(
        institution_id=tenant.id,
        project_id=project_id,
        evidence_id=payload.evidence_id,
        user_id=user.id,
    )
    return build_response(
        data={"project_id": str(pe.project_id), "evidence_id": str(pe.evidence_id)},
        request=request,
    )


@router.post(
    "/projects/{project_id}/verify",
    response_model=ApiResponse[ProjectResponse],
    summary="Verify Project (Faculty / Admin Gate)",
)
async def verify_project(
    request: Request,
    project_id: uuid.UUID,
    payload: ProjectVerifyRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ProjectResponse]:
    service = PlacementService(session)
    project = await service.verify_project(
        institution_id=tenant.id,
        project_id=project_id,
        verifier_user_id=user.id,
        is_verified=payload.is_verified,
        verification_notes=payload.verification_notes or "",
    )
    return build_response(data=ProjectResponse.model_validate(project), request=request)


@router.post(
    "/projects/{project_id}/revoke",
    response_model=ApiResponse[ProjectResponse],
    summary="Revoke Project Verification",
)
async def revoke_project_verification(
    request: Request,
    project_id: uuid.UUID,
    payload: ProjectRevokeRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ProjectResponse]:
    service = PlacementService(session)
    project = await service.revoke_project_verification(
        institution_id=tenant.id,
        project_id=project_id,
        revoker_user_id=user.id,
        revocation_reason=payload.revocation_reason,
    )
    return build_response(data=ProjectResponse.model_validate(project), request=request)


# =============================================================================
# 2. PORTFOLIO BUILDER
# =============================================================================
@router.get(
    "/portfolios/me",
    response_model=ApiResponse[PortfolioResponse],
    summary="Get Current User Portfolio Profile",
)
async def get_my_portfolio(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[PortfolioResponse]:
    service = PlacementService(session)
    portfolio = await service.get_or_create_portfolio(tenant.id, user)
    return build_response(data=PortfolioResponse.model_validate(portfolio), request=request)


@router.put(
    "/portfolios/me",
    response_model=ApiResponse[PortfolioResponse],
    summary="Update Portfolio Profile",
)
async def update_my_portfolio(
    request: Request,
    payload: PortfolioUpdateRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[PortfolioResponse]:
    service = PlacementService(session)
    portfolio = await service.update_portfolio(
        institution_id=tenant.id,
        student_user_id=user.id,
        headline=payload.headline,
        bio=payload.bio,
        visibility=payload.visibility,
        curated_project_ids=payload.curated_project_ids,
        featured_skill_ids=payload.featured_skill_ids,
        social_links=payload.social_links,
        custom_domain=payload.custom_domain,
    )
    return build_response(data=PortfolioResponse.model_validate(portfolio), request=request)


@router.post(
    "/portfolios/me/publish",
    response_model=ApiResponse[PortfolioResponse],
    summary="Publish or Unpublish Portfolio",
)
async def publish_my_portfolio(
    request: Request,
    payload: PortfolioPublishRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[PortfolioResponse]:
    service = PlacementService(session)
    portfolio = await service.publish_portfolio(
        institution_id=tenant.id,
        student_user_id=user.id,
        publish=payload.is_published,
    )
    return build_response(data=PortfolioResponse.model_validate(portfolio), request=request)


@router.get(
    "/portfolios/{slug}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="View Portfolio by Slug",
)
async def get_portfolio_by_slug(
    request: Request,
    slug: str,
    tenant: Institution = Depends(get_current_tenant),
    user: Optional[User] = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[Dict[str, Any]]:
    service = PlacementService(session)
    data = await service.get_portfolio_by_slug(
        institution_id=tenant.id,
        slug=slug,
        viewer_user=user,
    )
    return build_response(data=data, request=request)


# =============================================================================
# 3. CAREER GOALS & READINESS
# =============================================================================
@router.get(
    "/career-goals/me",
    response_model=ApiResponse[Optional[CareerGoalResponse]],
    summary="Get Student Active Career Goal",
)
async def get_my_career_goal(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[Optional[CareerGoalResponse]]:
    service = PlacementService(session)
    goal = await service.get_student_career_goal(tenant.id, user.id)
    return build_response(
        data=CareerGoalResponse.model_validate(goal) if goal else None,
        request=request,
    )


@router.post(
    "/career-goals/me",
    response_model=ApiResponse[CareerGoalResponse],
    summary="Create or Update Student Career Goal",
)
async def set_my_career_goal(
    request: Request,
    payload: CareerGoalRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CareerGoalResponse]:
    service = PlacementService(session)
    goal = await service.create_or_update_career_goal(
        institution_id=tenant.id,
        student_user_id=user.id,
        target_role=payload.target_role,
        target_industry=payload.target_industry or "",
        target_companies=payload.target_companies,
        required_skill_ids=payload.required_skill_ids,
    )
    return build_response(data=CareerGoalResponse.model_validate(goal), request=request)


@router.post(
    "/career-readiness/calculate",
    response_model=ApiResponse[CareerReadinessResponse],
    summary="Compute Deterministic Career Readiness",
)
async def calculate_career_readiness(
    request: Request,
    student_id: Optional[uuid.UUID] = Query(default=None),
    career_goal_id: Optional[uuid.UUID] = Query(default=None),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CareerReadinessResponse]:
    service = PlacementService(session)
    target_student_id = student_id if (student_id and user.roles[0] in ["SUPER_ADMIN", "INSTITUTION_ADMIN", "HOD", "FACULTY", "PLACEMENT_OFFICER"]) else user.id

    readiness = await service.compute_career_readiness(
        institution_id=tenant.id,
        student_user_id=target_student_id,
        career_goal_id=career_goal_id,
    )
    return build_response(data=CareerReadinessResponse.model_validate(readiness), request=request)


# =============================================================================
# 4. PLACEMENT TALENT DISCOVERY & ANALYTICS
# =============================================================================
@router.get(
    "/placement/talent-pool",
    response_model=ApiResponse[List[TalentCandidateResponse]],
    summary="Placement Officer Talent Discovery Pool",
)
async def search_talent_pool(
    request: Request,
    min_readiness: Optional[float] = Query(default=None, ge=0.0, le=1.0),
    target_role: Optional[str] = Query(default=None),
    skill_id: Optional[uuid.UUID] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.PLACEMENT_OFFICER)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[TalentCandidateResponse]]:
    service = PlacementService(session)
    offset = (page - 1) * page_size
    candidates = await service.search_talent_pool(
        institution_id=tenant.id,
        min_readiness=min_readiness,
        target_role=target_role,
        skill_id=skill_id,
        limit=page_size,
        offset=offset,
    )
    data = [TalentCandidateResponse.model_validate(c) for c in candidates]
    return build_response(
        data=data,
        request=request,
        pagination=PaginationMeta(page=page, page_size=page_size, total_records=len(data)),
    )


@router.get(
    "/placement/readiness-analytics",
    response_model=ApiResponse[PlacementAnalyticsResponse],
    summary="Placement Readiness Institutional Analytics",
)
async def get_placement_readiness_analytics(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.PLACEMENT_OFFICER)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[PlacementAnalyticsResponse]:
    service = PlacementService(session)
    analytics = await service.get_placement_readiness_analytics(tenant.id)
    return build_response(data=PlacementAnalyticsResponse.model_validate(analytics), request=request)
