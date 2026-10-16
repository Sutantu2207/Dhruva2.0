"""Dhruva.AI V2 — Mastery, Skills & Learning Evidence API Endpoints.

Prefix: /institutions/{institution_slug}/...
Enforces:
- Strict multi-tenant isolation.
- RBAC permissions (staff manage skills/concepts and verify evidence; students submit evidence and complete reviews).
- Deterministic mastery score updates.
"""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.mastery.mastery_service import MasteryService
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
from src.interfaces.http.schemas.mastery import (
    ConceptCreateRequest,
    ConceptPrerequisiteCreateRequest,
    ConceptPrerequisiteResponse,
    ConceptResponse,
    ConceptSkillLinkRequest,
    EvidenceResponse,
    EvidenceSubmitRequest,
    EvidenceVerifyRequest,
    LearningOutcomeCreateRequest,
    LearningOutcomeResponse,
    MasteryRecordResponse,
    ReviewCompleteRequest,
    ReviewScheduleResponse,
    SkillCreateRequest,
    SkillResponse,
)


router = APIRouter(prefix="/institutions/{institution_slug}", tags=["Mastery & Learning Evidence"])


# =============================================================================
# CONCEPTS & PREREQUISITES
# =============================================================================
@router.post(
    "/concepts",
    response_model=ApiResponse[ConceptResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Concept",
)
async def create_concept(
    request: Request,
    payload: ConceptCreateRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ConceptResponse]:
    service = MasteryService(session)
    concept = await service.create_concept(
        institution_id=tenant.id,
        code=payload.code,
        name=payload.name,
        description=payload.description or "",
        bloom_level=payload.bloom_level,
        department_id=payload.department_id,
        course_id=payload.course_id,
        parent_concept_id=payload.parent_concept_id,
    )
    return build_response(data=ConceptResponse.model_validate(concept), request=request)


@router.get(
    "/concepts",
    response_model=ApiResponse[List[ConceptResponse]],
    summary="List Concepts",
)
async def list_concepts(
    request: Request,
    course_id: Optional[uuid.UUID] = Query(default=None),
    department_id: Optional[uuid.UUID] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[ConceptResponse]]:
    service = MasteryService(session)
    offset = (page - 1) * page_size
    concepts = await service.list_concepts(
        institution_id=tenant.id,
        course_id=course_id,
        department_id=department_id,
        limit=page_size,
        offset=offset,
    )
    data = [ConceptResponse.model_validate(c) for c in concepts]
    return build_response(
        data=data,
        request=request,
        pagination=PaginationMeta(page=page, page_size=page_size, total_records=len(data)),
    )


@router.post(
    "/concepts/prerequisites",
    response_model=ApiResponse[ConceptPrerequisiteResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Concept Prerequisite Link",
)
async def create_concept_prerequisite(
    request: Request,
    payload: ConceptPrerequisiteCreateRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ConceptPrerequisiteResponse]:
    service = MasteryService(session)
    prereq = await service.create_concept_prerequisite(
        institution_id=tenant.id,
        concept_id=payload.concept_id,
        prerequisite_concept_id=payload.prerequisite_concept_id,
    )
    return build_response(data=ConceptPrerequisiteResponse.model_validate(prereq), request=request)


@router.get(
    "/concepts/prerequisites",
    response_model=ApiResponse[List[ConceptPrerequisiteResponse]],
    summary="List Concept Prerequisites",
)
async def list_concept_prerequisites(
    request: Request,
    concept_id: Optional[uuid.UUID] = Query(default=None),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[ConceptPrerequisiteResponse]]:
    service = MasteryService(session)
    prereqs = await service.list_concept_prerequisites(
        institution_id=tenant.id,
        concept_id=concept_id,
    )
    data = [ConceptPrerequisiteResponse.model_validate(p) for p in prereqs]
    return build_response(data=data, request=request)


# =============================================================================
# LEARNING OUTCOMES
# =============================================================================
@router.post(
    "/learning-outcomes",
    response_model=ApiResponse[LearningOutcomeResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Learning Outcome",
)
async def create_learning_outcome(
    request: Request,
    payload: LearningOutcomeCreateRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[LearningOutcomeResponse]:
    service = MasteryService(session)
    outcome = await service.create_learning_outcome(
        institution_id=tenant.id,
        code=payload.code,
        statement=payload.statement,
        bloom_level=payload.bloom_level,
        course_id=payload.course_id,
        concept_id=payload.concept_id,
        skill_id=payload.skill_id,
    )
    return build_response(data=LearningOutcomeResponse.model_validate(outcome), request=request)


@router.get(
    "/learning-outcomes",
    response_model=ApiResponse[List[LearningOutcomeResponse]],
    summary="List Learning Outcomes",
)
async def list_learning_outcomes(
    request: Request,
    course_id: Optional[uuid.UUID] = Query(default=None),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[LearningOutcomeResponse]]:
    service = MasteryService(session)
    outcomes = await service.list_learning_outcomes(
        institution_id=tenant.id,
        course_id=course_id,
    )
    data = [LearningOutcomeResponse.model_validate(o) for o in outcomes]
    return build_response(data=data, request=request)


# =============================================================================
# SKILLS
# =============================================================================
@router.post(
    "/skills",
    response_model=ApiResponse[SkillResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Skill",
)
async def create_skill(
    request: Request,
    payload: SkillCreateRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[SkillResponse]:
    service = MasteryService(session)
    skill = await service.create_skill(
        institution_id=tenant.id,
        code=payload.code,
        name=payload.name,
        category=payload.category,
        description=payload.description or "",
    )
    return build_response(data=SkillResponse.model_validate(skill), request=request)


@router.get(
    "/skills",
    response_model=ApiResponse[List[SkillResponse]],
    summary="List Skills",
)
async def list_skills(
    request: Request,
    category: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[SkillResponse]]:
    service = MasteryService(session)
    offset = (page - 1) * page_size
    skills = await service.list_skills(
        institution_id=tenant.id,
        category=category,
        limit=page_size,
        offset=offset,
    )
    data = [SkillResponse.model_validate(s) for s in skills]
    return build_response(
        data=data,
        request=request,
        pagination=PaginationMeta(page=page, page_size=page_size, total_records=len(data)),
    )


@router.post(
    "/concepts/link-skill",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Link Concept to Skill",
)
async def link_concept_to_skill(
    request: Request,
    payload: ConceptSkillLinkRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[Dict[str, Any]]:
    service = MasteryService(session)
    link = await service.link_concept_to_skill(
        institution_id=tenant.id,
        concept_id=payload.concept_id,
        skill_id=payload.skill_id,
        weight=payload.weight,
    )
    return build_response(
        data={"concept_id": str(link.concept_id), "skill_id": str(link.skill_id), "weight": link.weight},
        request=request,
    )


# =============================================================================
# LEARNING EVIDENCE
# =============================================================================
@router.post(
    "/evidence/submit",
    response_model=ApiResponse[EvidenceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit Learning Evidence",
)
async def submit_learning_evidence(
    request: Request,
    payload: EvidenceSubmitRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.STUDENT, SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[EvidenceResponse]:
    service = MasteryService(session)
    evidence = await service.submit_learning_evidence(
        institution_id=tenant.id,
        student_user_id=user.id,
        skill_id=payload.skill_id,
        evidence_type=payload.evidence_type,
        title=payload.title,
        description=payload.description or "",
        artifact_url=payload.artifact_url,
        concept_id=payload.concept_id,
        file_size_bytes=payload.file_size_bytes,
    )
    return build_response(data=EvidenceResponse.model_validate(evidence), request=request)


@router.post(
    "/evidence/{evidence_id}/verify",
    response_model=ApiResponse[EvidenceResponse],
    summary="Verify Learning Evidence",
)
async def verify_learning_evidence(
    request: Request,
    evidence_id: uuid.UUID,
    payload: EvidenceVerifyRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[EvidenceResponse]:
    service = MasteryService(session)
    evidence = await service.verify_learning_evidence(
        institution_id=tenant.id,
        evidence_id=evidence_id,
        verifier_user_id=user.id,
        is_verified=payload.is_verified,
        notes=payload.verification_notes or "",
    )
    return build_response(data=EvidenceResponse.model_validate(evidence), request=request)


@router.get(
    "/students/{student_id}/evidence",
    response_model=ApiResponse[List[EvidenceResponse]],
    summary="Get Student Learning Evidence History",
)
async def get_student_evidence(
    request: Request,
    student_id: uuid.UUID,
    skill_id: Optional[uuid.UUID] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[EvidenceResponse]]:
    service = MasteryService(session)
    offset = (page - 1) * page_size
    evidences = await service.get_student_evidence(
        institution_id=tenant.id,
        student_user_id=student_id,
        skill_id=skill_id,
        limit=page_size,
        offset=offset,
    )
    data = [EvidenceResponse.model_validate(e) for e in evidences]
    return build_response(
        data=data,
        request=request,
        pagination=PaginationMeta(page=page, page_size=page_size, total_records=len(data)),
    )


@router.post(
    "/assessments/{result_id}/sync-evidence",
    response_model=ApiResponse[List[EvidenceResponse]],
    summary="Sync Evidence from Assessment Result",
)
async def sync_evidence_from_assessment_result(
    request: Request,
    result_id: uuid.UUID,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[EvidenceResponse]]:
    service = MasteryService(session)
    synced = await service.sync_evidence_from_assessment_result(
        institution_id=tenant.id,
        result_id=result_id,
    )
    data = [EvidenceResponse.model_validate(e) for e in synced]
    return build_response(data=data, request=request)


# =============================================================================
# MASTERY PROFILE
# =============================================================================
@router.get(
    "/students/{student_id}/mastery",
    response_model=ApiResponse[List[MasteryRecordResponse]],
    summary="Get Student Mastery Profile",
)
async def get_student_mastery_profile(
    request: Request,
    student_id: uuid.UUID,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[MasteryRecordResponse]]:
    service = MasteryService(session)
    records = await service.get_student_mastery_profile(
        institution_id=tenant.id,
        student_user_id=student_id,
    )
    data = [MasteryRecordResponse.model_validate(r) for r in records]
    return build_response(data=data, request=request)


# =============================================================================
# SPACED REVIEWS (SM-2)
# =============================================================================
@router.post(
    "/reviews/schedule",
    response_model=ApiResponse[ReviewScheduleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Schedule Concept Spaced Review",
)
async def schedule_concept_review(
    request: Request,
    concept_id: uuid.UUID = Query(...),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ReviewScheduleResponse]:
    service = MasteryService(session)
    sched = await service.schedule_concept_review(
        institution_id=tenant.id,
        student_user_id=user.id,
        concept_id=concept_id,
    )
    return build_response(data=ReviewScheduleResponse.model_validate(sched), request=request)


@router.get(
    "/reviews/me",
    response_model=ApiResponse[List[ReviewScheduleResponse]],
    summary="Get Current User Pending Spaced Reviews",
)
async def get_my_pending_reviews(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[ReviewScheduleResponse]]:
    service = MasteryService(session)
    schedules = await service.get_student_pending_reviews(
        institution_id=tenant.id,
        student_user_id=user.id,
    )
    data = [ReviewScheduleResponse.model_validate(s) for s in schedules]
    return build_response(data=data, request=request)


@router.post(
    "/reviews/{schedule_id}/complete",
    response_model=ApiResponse[ReviewScheduleResponse],
    summary="Complete Spaced Review",
)
async def complete_spaced_review(
    request: Request,
    schedule_id: uuid.UUID,
    payload: ReviewCompleteRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ReviewScheduleResponse]:
    service = MasteryService(session)
    sched = await service.complete_concept_review(
        institution_id=tenant.id,
        student_user_id=user.id,
        schedule_id=schedule_id,
        quality_rating=payload.quality_rating,
    )
    return build_response(data=ReviewScheduleResponse.model_validate(sched), request=request)
