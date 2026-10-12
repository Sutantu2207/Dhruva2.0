"""Dhruva.AI V2 — Curriculum, Syllabus & Learning Content API Endpoints.

Prefix: /institutions/{institution_slug}/...
Enforces strict tenant scoping, role-based workflows, and standardized envelope responses.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.curriculum.curriculum_service import CurriculumService
from src.core.errors import PermissionDeniedError
from src.domain.identity.models import Institution, User
from src.domain.identity.roles import SystemRole
from src.infrastructure.persistence.postgres.database import get_db_session
from src.interfaces.http.dependencies import (
    build_response,
    get_current_tenant,
    get_current_user,
    require_roles,
)
from src.interfaces.http.schemas.curriculum import (
    CurriculumCreateRequest,
    CurriculumDetailResponse,
    CurriculumResponse,
    CurriculumStatusUpdateRequest,
    LearningResourceCreateRequest,
    LearningResourceResponse,
    LessonCreateRequest,
    LessonDetailResponse,
    LessonResponse,
    ModuleCreateRequest,
    ModuleDetailResponse,
    ModuleResponse,
)
from src.interfaces.http.schemas.envelope import ApiResponse, PaginationMeta


router = APIRouter(prefix="/institutions/{institution_slug}", tags=["Curriculum & Content Management"])


# =========================================================================
# CURRICULUM ENDPOINTS
# =========================================================================
@router.get(
    "/courses/{course_id}/curriculums",
    response_model=ApiResponse[List[CurriculumResponse]],
    summary="List Curriculum Versions for Course",
)
async def list_course_curriculums(
    course_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[CurriculumResponse]]:
    service = CurriculumService(session)
    curriculums = await service.list_curriculums_for_course(tenant.id, course_id)
    data = [CurriculumResponse.model_validate(c) for c in curriculums]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/courses/{course_id}/curriculums",
    response_model=ApiResponse[CurriculumResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create New Curriculum Version",
)
async def create_course_curriculum(
    course_id: uuid.UUID,
    payload: CurriculumCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(
        require_roles(
            SystemRole.SUPER_ADMIN,
            SystemRole.INSTITUTION_ADMIN,
            SystemRole.HOD,
            SystemRole.FACULTY,
        )
    ),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CurriculumResponse]:
    service = CurriculumService(session)
    created = await service.create_curriculum(
        institution_id=tenant.id,
        course_id=course_id,
        title=payload.title,
        program_id=payload.program_id,
        academic_year_id=payload.academic_year_id,
        description=payload.description,
        learning_objectives=payload.learning_objectives,
        actor_user_id=caller.id,
    )
    return build_response(data=CurriculumResponse.model_validate(created), request=request)


@router.get(
    "/curriculums",
    response_model=ApiResponse[List[CurriculumResponse]],
    summary="List Institution Curriculums",
)
async def list_curriculums(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[CurriculumResponse]]:
    service = CurriculumService(session)
    curriculums = await service.list_institution_curriculums(tenant.id, status=status_filter)
    data = [CurriculumResponse.model_validate(c) for c in curriculums]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.get(
    "/curriculums/{curriculum_id}",
    response_model=ApiResponse[CurriculumDetailResponse],
    summary="Get Curriculum Details with Syllabus Tree",
)
async def get_curriculum_details(
    curriculum_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CurriculumDetailResponse]:
    service = CurriculumService(session)
    curriculum = await service.get_curriculum(tenant.id, curriculum_id)
    modules = await service.list_modules_for_curriculum(tenant.id, curriculum_id)

    module_details: List[ModuleDetailResponse] = []
    for m in modules:
        lessons = await service.list_lessons_for_module(tenant.id, m.id)
        lesson_details: List[LessonDetailResponse] = []
        for l in lessons:
            resources = await service.list_resources_for_lesson(tenant.id, l.id)
            lesson_details.append(
                LessonDetailResponse(
                    id=l.id,
                    institution_id=l.institution_id,
                    module_id=l.module_id,
                    sequence_order=l.sequence_order,
                    title=l.title,
                    content_markdown=l.content_markdown,
                    lesson_type=l.lesson_type,
                    duration_minutes=l.duration_minutes,
                    learning_resources=[LearningResourceResponse.model_validate(r) for r in resources],
                    created_at=l.created_at,
                    updated_at=l.updated_at,
                )
            )
        module_details.append(
            ModuleDetailResponse(
                id=m.id,
                institution_id=m.institution_id,
                curriculum_id=m.curriculum_id,
                sequence_order=m.sequence_order,
                title=m.title,
                description=m.description,
                estimated_hours=m.estimated_hours,
                learning_outcomes=m.learning_outcomes,
                lessons=lesson_details,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
        )

    dto = CurriculumDetailResponse(
        id=curriculum.id,
        institution_id=curriculum.institution_id,
        course_id=curriculum.course_id,
        program_id=curriculum.program_id,
        academic_year_id=curriculum.academic_year_id,
        title=curriculum.title,
        version=curriculum.version,
        status=curriculum.status,
        description=curriculum.description,
        learning_objectives=curriculum.learning_objectives,
        approved_by=curriculum.approved_by,
        approved_at=curriculum.approved_at,
        provenance_id=curriculum.provenance_id,
        modules=module_details,
        created_at=curriculum.created_at,
        updated_at=curriculum.updated_at,
    )
    return build_response(data=dto, request=request)


@router.patch(
    "/curriculums/{curriculum_id}/status",
    response_model=ApiResponse[CurriculumResponse],
    summary="Update Curriculum Publication Status",
)
async def update_curriculum_status(
    curriculum_id: uuid.UUID,
    payload: CurriculumStatusUpdateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CurriculumResponse]:
    target = payload.status.strip().upper()
    user_roles = {ur.role.code for ur in caller.user_roles if ur.role}

    # Approving or publishing requires administrative privileges
    if target in ("APPROVED", "PUBLISHED"):
        admin_roles = {SystemRole.SUPER_ADMIN.value, SystemRole.INSTITUTION_ADMIN.value, SystemRole.HOD.value}
        if not user_roles.intersection(admin_roles):
            raise PermissionDeniedError(
                f"Approving or publishing curriculum requires one of: {', '.join(admin_roles)}",
                code="INSUFFICIENT_ROLE",
            )
    else:
        # Draft to in-review allowed for faculty as well
        allowed_roles = {
            SystemRole.SUPER_ADMIN.value,
            SystemRole.INSTITUTION_ADMIN.value,
            SystemRole.HOD.value,
            SystemRole.FACULTY.value,
        }
        if not user_roles.intersection(allowed_roles):
            raise PermissionDeniedError("Insufficient role to change curriculum status", code="INSUFFICIENT_ROLE")

    service = CurriculumService(session)
    updated = await service.update_curriculum_status(
        institution_id=tenant.id,
        curriculum_id=curriculum_id,
        target_status=target,
        actor_user_id=caller.id,
    )
    return build_response(data=CurriculumResponse.model_validate(updated), request=request)


# =========================================================================
# MODULE ENDPOINTS
# =========================================================================
@router.get(
    "/curriculums/{curriculum_id}/modules",
    response_model=ApiResponse[List[ModuleResponse]],
    summary="List Curriculum Modules",
)
async def list_modules(
    curriculum_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[ModuleResponse]]:
    service = CurriculumService(session)
    modules = await service.list_modules_for_curriculum(tenant.id, curriculum_id)
    data = [ModuleResponse.model_validate(m) for m in modules]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/curriculums/{curriculum_id}/modules",
    response_model=ApiResponse[ModuleResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Curriculum Module",
)
async def create_module(
    curriculum_id: uuid.UUID,
    payload: ModuleCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(
        require_roles(
            SystemRole.SUPER_ADMIN,
            SystemRole.INSTITUTION_ADMIN,
            SystemRole.HOD,
            SystemRole.FACULTY,
        )
    ),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ModuleResponse]:
    service = CurriculumService(session)
    created = await service.create_module(
        institution_id=tenant.id,
        curriculum_id=curriculum_id,
        title=payload.title,
        sequence_order=payload.sequence_order,
        description=payload.description,
        estimated_hours=payload.estimated_hours,
        learning_outcomes=payload.learning_outcomes,
        actor_user_id=caller.id,
    )
    return build_response(data=ModuleResponse.model_validate(created), request=request)


# =========================================================================
# LESSON ENDPOINTS
# =========================================================================
@router.get(
    "/modules/{module_id}/lessons",
    response_model=ApiResponse[List[LessonResponse]],
    summary="List Lessons in Module",
)
async def list_lessons(
    module_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[LessonResponse]]:
    service = CurriculumService(session)
    lessons = await service.list_lessons_for_module(tenant.id, module_id)
    data = [LessonResponse.model_validate(l) for l in lessons]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/modules/{module_id}/lessons",
    response_model=ApiResponse[LessonResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Lesson / Topic in Module",
)
async def create_lesson(
    module_id: uuid.UUID,
    payload: LessonCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(
        require_roles(
            SystemRole.SUPER_ADMIN,
            SystemRole.INSTITUTION_ADMIN,
            SystemRole.HOD,
            SystemRole.FACULTY,
        )
    ),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[LessonResponse]:
    service = CurriculumService(session)
    created = await service.create_lesson(
        institution_id=tenant.id,
        module_id=module_id,
        title=payload.title,
        sequence_order=payload.sequence_order,
        content_markdown=payload.content_markdown,
        lesson_type=payload.lesson_type,
        duration_minutes=payload.duration_minutes,
        actor_user_id=caller.id,
    )
    return build_response(data=LessonResponse.model_validate(created), request=request)


# =========================================================================
# LEARNING RESOURCE ENDPOINTS
# =========================================================================
@router.get(
    "/lessons/{lesson_id}/resources",
    response_model=ApiResponse[List[LearningResourceResponse]],
    summary="List Learning Resources for Lesson",
)
async def list_resources(
    lesson_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[LearningResourceResponse]]:
    service = CurriculumService(session)
    resources = await service.list_resources_for_lesson(tenant.id, lesson_id)
    data = [LearningResourceResponse.model_validate(r) for r in resources]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/lessons/{lesson_id}/resources",
    response_model=ApiResponse[LearningResourceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Attach Learning Resource to Lesson",
)
async def create_resource(
    lesson_id: uuid.UUID,
    payload: LearningResourceCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(
        require_roles(
            SystemRole.SUPER_ADMIN,
            SystemRole.INSTITUTION_ADMIN,
            SystemRole.HOD,
            SystemRole.FACULTY,
        )
    ),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[LearningResourceResponse]:
    service = CurriculumService(session)
    created = await service.create_learning_resource(
        institution_id=tenant.id,
        lesson_id=lesson_id,
        title=payload.title,
        resource_type=payload.resource_type,
        storage_uri=payload.storage_uri,
        external_url=payload.external_url,
        resource_metadata=payload.resource_metadata,
        actor_user_id=caller.id,
    )
    return build_response(data=LearningResourceResponse.model_validate(created), request=request)
