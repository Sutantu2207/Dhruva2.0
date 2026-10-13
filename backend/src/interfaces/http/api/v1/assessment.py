"""Dhruva.AI V2 — Assessment, Question Bank & Grading API Endpoints.

Prefix: /institutions/{institution_slug}/...
Enforces:
- RBAC permissions for authoring, publishing, and manual evaluation.
- Multi-tenant data segregation.
- Strict prevention of answer key leakage in student-facing endpoints.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.assessment.assessment_service import AssessmentService
from src.domain.identity.models import Institution, User
from src.domain.identity.roles import SystemRole
from src.infrastructure.persistence.postgres.database import get_db_session
from src.interfaces.http.dependencies import (
    build_response,
    get_current_tenant,
    get_current_user,
    require_roles,
)
from src.interfaces.http.schemas.assessment import (
    AssessmentCreateRequest,
    AssessmentQuestionAddRequest,
    AssessmentQuestionResponse,
    AssessmentResponse,
    AssessmentResultResponse,
    AssessmentStudentDetailResponse,
    ManualGradeRequest,
    QuestionAdminResponse,
    QuestionBankCreateRequest,
    QuestionBankResponse,
    QuestionCreateRequest,
    SubmissionCreateRequest,
    SubmissionResponse,
)
from src.interfaces.http.schemas.envelope import ApiResponse, PaginationMeta


router = APIRouter(prefix="/institutions/{institution_slug}", tags=["Assessments & Question Banks"])


# =========================================================================
# QUESTION BANKS
# =========================================================================
@router.get(
    "/question-banks",
    response_model=ApiResponse[List[QuestionBankResponse]],
    summary="List Question Banks",
)
async def list_question_banks(
    request: Request,
    course_id: Optional[uuid.UUID] = Query(default=None),
    department_id: Optional[uuid.UUID] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[QuestionBankResponse]]:
    service = AssessmentService(session)
    offset = (page - 1) * page_size
    banks = await service.list_question_banks(
        institution_id=tenant.id,
        course_id=course_id,
        department_id=department_id,
        limit=page_size,
        offset=offset,
    )
    data = [QuestionBankResponse.model_validate(b) for b in banks]
    pagination = PaginationMeta(page=page, page_size=page_size, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/question-banks",
    response_model=ApiResponse[QuestionBankResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Question Bank",
)
async def create_question_bank(
    payload: QuestionBankCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[QuestionBankResponse]:
    service = AssessmentService(session)
    bank = await service.create_question_bank(
        institution_id=tenant.id,
        title=payload.title,
        creator_user=user,
        description=payload.description or "",
        course_id=payload.course_id,
        department_id=payload.department_id,
    )
    return build_response(data=QuestionBankResponse.model_validate(bank), request=request)


@router.get(
    "/question-banks/{bank_id}",
    response_model=ApiResponse[QuestionBankResponse],
    summary="Get Question Bank Detail",
)
async def get_question_bank(
    bank_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[QuestionBankResponse]:
    service = AssessmentService(session)
    bank = await service.get_question_bank(tenant.id, bank_id)
    return build_response(data=QuestionBankResponse.model_validate(bank), request=request)


# =========================================================================
# QUESTIONS
# =========================================================================
@router.post(
    "/question-banks/{bank_id}/questions",
    response_model=ApiResponse[QuestionAdminResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Question in Bank",
)
async def create_question(
    bank_id: uuid.UUID,
    payload: QuestionCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[QuestionAdminResponse]:
    service = AssessmentService(session)
    question = await service.create_question(
        institution_id=tenant.id,
        question_bank_id=bank_id,
        question_type=payload.question_type,
        prompt_text=payload.prompt_text,
        answer_key=payload.answer_key,
        creator_user=user,
        options=payload.options,
        points=payload.points,
        difficulty=payload.difficulty,
        explanation=payload.explanation or "",
        concept_id=payload.concept_id,
        skill_id=payload.skill_id,
    )
    return build_response(data=QuestionAdminResponse.model_validate(question), request=request)


@router.get(
    "/question-banks/{bank_id}/questions",
    response_model=ApiResponse[List[QuestionAdminResponse]],
    summary="List Questions in Question Bank",
)
async def list_questions_in_bank(
    bank_id: uuid.UUID,
    request: Request,
    question_type: Optional[str] = Query(default=None),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[QuestionAdminResponse]]:
    service = AssessmentService(session)
    questions = await service.list_questions_by_bank(tenant.id, bank_id, question_type=question_type)
    data = [QuestionAdminResponse.model_validate(q) for q in questions]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


# =========================================================================
# ASSESSMENTS
# =========================================================================
@router.post(
    "/assessments",
    response_model=ApiResponse[AssessmentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Assessment",
)
async def create_assessment(
    payload: AssessmentCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[AssessmentResponse]:
    service = AssessmentService(session)
    assessment = await service.create_assessment(
        institution_id=tenant.id,
        course_offering_id=payload.course_offering_id,
        title=payload.title,
        publish_at=payload.publish_at,
        due_at=payload.due_at,
        creator_user=user,
        instructions=payload.instructions or "",
        assessment_type=payload.assessment_type,
        duration_minutes=payload.duration_minutes,
        passing_percentage=payload.passing_percentage,
        max_attempts=payload.max_attempts,
    )
    return build_response(data=AssessmentResponse.model_validate(assessment), request=request)


@router.get(
    "/assessments",
    response_model=ApiResponse[List[AssessmentResponse]],
    summary="List Assessments",
)
async def list_assessments(
    request: Request,
    course_offering_id: Optional[uuid.UUID] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[AssessmentResponse]]:
    service = AssessmentService(session)
    offset = (page - 1) * page_size
    assessments = await service.list_assessments(
        institution_id=tenant.id,
        course_offering_id=course_offering_id,
        status=status_filter,
        limit=page_size,
        offset=offset,
    )
    total_count = await service.repo.count_assessments(
        institution_id=tenant.id,
        course_offering_id=course_offering_id,
        status=status_filter,
    )
    data = [AssessmentResponse.model_validate(a) for a in assessments]
    pagination = PaginationMeta(page=page, page_size=page_size, total_records=total_count)
    return build_response(data=data, request=request, pagination=pagination)


@router.get(
    "/assessments/{assessment_id}",
    summary="Get Assessment Detail (Role-Sensitive / Sanitized for Students)",
)
async def get_assessment(
    assessment_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
):
    service = AssessmentService(session)
    assessment = await service.get_assessment(tenant.id, assessment_id)

    is_student_only = (
        SystemRole.STUDENT.value in user.roles
        and not any(r in (SystemRole.SUPER_ADMIN.value, SystemRole.INSTITUTION_ADMIN.value, SystemRole.HOD.value, SystemRole.FACULTY.value) for r in user.roles)
    )

    if is_student_only:
        # Sanitized response with zero answer keys!
        sanitized = AssessmentStudentDetailResponse.model_validate(assessment)
        return build_response(data=sanitized, request=request)
    else:
        # Full response for authorized faculty / admin
        return build_response(data=AssessmentResponse.model_validate(assessment), request=request)


@router.post(
    "/assessments/{assessment_id}/questions",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Add Question to Assessment",
)
async def add_question_to_assessment(
    assessment_id: uuid.UUID,
    payload: AssessmentQuestionAddRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[dict]:
    service = AssessmentService(session)
    link = await service.add_question_to_assessment(
        institution_id=tenant.id,
        assessment_id=assessment_id,
        question_id=payload.question_id,
        points=payload.points,
        sort_order=payload.sort_order,
    )
    return build_response(
        data={
            "assessment_id": link.assessment_id,
            "question_id": link.question_id,
            "points": link.points,
            "sort_order": link.sort_order,
        },
        request=request,
    )


@router.post(
    "/assessments/{assessment_id}/publish",
    response_model=ApiResponse[AssessmentResponse],
    summary="Publish Assessment to Enrolled Students",
)
async def publish_assessment(
    assessment_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[AssessmentResponse]:
    service = AssessmentService(session)
    assessment = await service.publish_assessment(tenant.id, assessment_id, publisher_user=user)
    return build_response(data=AssessmentResponse.model_validate(assessment), request=request)


# =========================================================================
# SUBMISSIONS & GRADING
# =========================================================================
@router.post(
    "/assessments/{assessment_id}/submit",
    response_model=ApiResponse[SubmissionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit Assessment Attempt & Execute Deterministic Grading",
)
async def submit_assessment(
    assessment_id: uuid.UUID,
    payload: SubmissionCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[SubmissionResponse]:
    service = AssessmentService(session)
    submission = await service.submit_assessment(
        institution_id=tenant.id,
        assessment_id=assessment_id,
        student_user=user,
        answers_payload=payload.answers_payload,
    )
    return build_response(data=SubmissionResponse.model_validate(submission), request=request)


@router.get(
    "/submissions/{submission_id}",
    response_model=ApiResponse[SubmissionResponse],
    summary="Get Submission Details & Itemized Grading Result",
)
async def get_submission(
    submission_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[SubmissionResponse]:
    service = AssessmentService(session)
    submission = await service.get_submission(tenant.id, submission_id, requesting_user=user)
    return build_response(data=SubmissionResponse.model_validate(submission), request=request)


@router.post(
    "/submissions/{submission_id}/grade-manual",
    response_model=ApiResponse[AssessmentResultResponse],
    summary="Record Manual Evaluation for Subjective Question",
)
@router.post(
    "/assessments/{assessment_id}/submissions/{submission_id}/grade-manual",
    response_model=ApiResponse[AssessmentResultResponse],
    summary="Record Manual Evaluation for Subjective Question (Nested)",
)
async def grade_manual_question(
    submission_id: uuid.UUID,
    payload: ManualGradeRequest,
    request: Request,
    assessment_id: Optional[uuid.UUID] = None,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[AssessmentResultResponse]:
    service = AssessmentService(session)
    result = await service.grade_manual_question(
        institution_id=tenant.id,
        submission_id=submission_id,
        question_id=payload.question_id,
        awarded_points=payload.awarded_points,
        reviewer_user=user,
        feedback=payload.feedback or "",
    )
    return build_response(data=AssessmentResultResponse.model_validate(result), request=request)


@router.get(
    "/assessments/{assessment_id}/submissions",
    response_model=ApiResponse[List[SubmissionResponse]],
    summary="List All Submissions for Assessment (Faculty/Admin)",
)
async def list_submissions_for_assessment(
    assessment_id: uuid.UUID,
    request: Request,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[SubmissionResponse]]:
    service = AssessmentService(session)
    offset = (page - 1) * page_size
    submissions = await service.repo.list_submissions_for_assessment(
        institution_id=tenant.id,
        assessment_id=assessment_id,
        status=status_filter,
        limit=page_size,
        offset=offset,
    )
    data = [SubmissionResponse.model_validate(s) for s in submissions]
    pagination = PaginationMeta(page=page, page_size=page_size, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)
