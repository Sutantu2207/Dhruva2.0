"""Dhruva.AI V2 — Academic Hierarchy & Course Catalog API Endpoints.

Prefix: /institutions/{institution_slug}/...
Enforces strict tenant scoping, RBAC checks, and standardized envelope responses.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.academic.academic_service import AcademicService
from src.domain.identity.models import Institution, User
from src.domain.identity.roles import SystemRole
from src.infrastructure.persistence.postgres.database import get_db_session
from src.interfaces.http.dependencies import (
    build_response,
    get_current_tenant,
    get_current_user,
    require_roles,
)
from src.interfaces.http.schemas.academic import (
    AcademicYearCreateRequest,
    AcademicYearResponse,
    BatchCreateRequest,
    BatchResponse,
    CourseCreateRequest,
    CourseOfferingCreateRequest,
    CourseOfferingResponse,
    CourseResponse,
    DepartmentCreateRequest,
    DepartmentResponse,
    ProgramCreateRequest,
    ProgramResponse,
    SectionCreateRequest,
    SectionResponse,
    SemesterCreateRequest,
    SemesterResponse,
    StudentEnrollmentCreateRequest,
    StudentEnrollmentResponse,
    TeachingAssignmentCreateRequest,
    TeachingAssignmentResponse,
)
from src.interfaces.http.schemas.envelope import ApiResponse, PaginationMeta


router = APIRouter(prefix="/institutions/{institution_slug}", tags=["Academic Structure & Catalog"])


# =========================================================================
# DEPARTMENTS
# =========================================================================
@router.get(
    "/departments",
    response_model=ApiResponse[List[DepartmentResponse]],
    summary="List Departments",
)
async def list_departments(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[DepartmentResponse]]:
    service = AcademicService(session)
    departments = await service.list_departments(tenant.id)
    data = [DepartmentResponse.model_validate(d) for d in departments]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/departments",
    response_model=ApiResponse[DepartmentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Department",
)
async def create_department(
    payload: DepartmentCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[DepartmentResponse]:
    service = AcademicService(session)
    created = await service.create_department(
        institution_id=tenant.id,
        code=payload.code,
        name=payload.name,
        hod_user_id=payload.hod_user_id,
        actor_user_id=caller.id,
    )
    return build_response(data=DepartmentResponse.model_validate(created), request=request)


@router.get(
    "/departments/{department_id}",
    response_model=ApiResponse[DepartmentResponse],
    summary="Get Department Details",
)
async def get_department(
    department_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[DepartmentResponse]:
    service = AcademicService(session)
    dept = await service.get_department(tenant.id, department_id)
    return build_response(data=DepartmentResponse.model_validate(dept), request=request)


# =========================================================================
# PROGRAMS
# =========================================================================
@router.get(
    "/programs",
    response_model=ApiResponse[List[ProgramResponse]],
    summary="List Academic Programs",
)
async def list_programs(
    request: Request,
    department_id: Optional[uuid.UUID] = Query(None, description="Filter by department"),
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[ProgramResponse]]:
    service = AcademicService(session)
    programs = await service.list_programs(tenant.id, department_id=department_id)
    data = [ProgramResponse.model_validate(p) for p in programs]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/programs",
    response_model=ApiResponse[ProgramResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Academic Program",
)
async def create_program(
    payload: ProgramCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ProgramResponse]:
    service = AcademicService(session)
    created = await service.create_program(
        institution_id=tenant.id,
        department_id=payload.department_id,
        code=payload.code,
        name=payload.name,
        degree_level=payload.degree_level,
        total_semesters=payload.total_semesters,
        actor_user_id=caller.id,
    )
    return build_response(data=ProgramResponse.model_validate(created), request=request)


@router.get(
    "/programs/{program_id}",
    response_model=ApiResponse[ProgramResponse],
    summary="Get Program Details",
)
async def get_program(
    program_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ProgramResponse]:
    service = AcademicService(session)
    prog = await service.get_program(tenant.id, program_id)
    return build_response(data=ProgramResponse.model_validate(prog), request=request)


# =========================================================================
# ACADEMIC YEARS & SEMESTERS
# =========================================================================
@router.get(
    "/academic-years",
    response_model=ApiResponse[List[AcademicYearResponse]],
    summary="List Academic Years",
)
async def list_academic_years(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[AcademicYearResponse]]:
    service = AcademicService(session)
    years = await service.list_academic_years(tenant.id)
    data = [AcademicYearResponse.model_validate(y) for y in years]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/academic-years",
    response_model=ApiResponse[AcademicYearResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Academic Year",
)
async def create_academic_year(
    payload: AcademicYearCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[AcademicYearResponse]:
    service = AcademicService(session)
    created = await service.create_academic_year(
        institution_id=tenant.id,
        code=payload.code,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_current=payload.is_current,
        actor_user_id=caller.id,
    )
    return build_response(data=AcademicYearResponse.model_validate(created), request=request)


@router.get(
    "/academic-years/{academic_year_id}/semesters",
    response_model=ApiResponse[List[SemesterResponse]],
    summary="List Semesters in Academic Year",
)
async def list_semesters(
    academic_year_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[SemesterResponse]]:
    service = AcademicService(session)
    semesters = await service.list_semesters(tenant.id, academic_year_id)
    data = [SemesterResponse.model_validate(s) for s in semesters]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/academic-years/{academic_year_id}/semesters",
    response_model=ApiResponse[SemesterResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Semester in Academic Year",
)
async def create_semester(
    academic_year_id: uuid.UUID,
    payload: SemesterCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[SemesterResponse]:
    service = AcademicService(session)
    created = await service.create_semester(
        institution_id=tenant.id,
        academic_year_id=academic_year_id,
        term_number=payload.term_number,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status,
        actor_user_id=caller.id,
    )
    return build_response(data=SemesterResponse.model_validate(created), request=request)


# =========================================================================
# BATCHES & SECTIONS
# =========================================================================
@router.get(
    "/batches",
    response_model=ApiResponse[List[BatchResponse]],
    summary="List Cohort Batches",
)
async def list_batches(
    request: Request,
    program_id: Optional[uuid.UUID] = Query(None, description="Filter by program"),
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[BatchResponse]]:
    service = AcademicService(session)
    batches = await service.list_batches(tenant.id, program_id=program_id)
    data = [BatchResponse.model_validate(b) for b in batches]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/batches",
    response_model=ApiResponse[BatchResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Cohort Batch",
)
async def create_batch(
    payload: BatchCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[BatchResponse]:
    service = AcademicService(session)
    created = await service.create_batch(
        institution_id=tenant.id,
        program_id=payload.program_id,
        name=payload.name,
        admission_year=payload.admission_year,
        graduation_year=payload.graduation_year,
        actor_user_id=caller.id,
    )
    return build_response(data=BatchResponse.model_validate(created), request=request)


@router.get(
    "/batches/{batch_id}/sections",
    response_model=ApiResponse[List[SectionResponse]],
    summary="List Sections in Batch",
)
async def list_sections(
    batch_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[SectionResponse]]:
    service = AcademicService(session)
    sections = await service.list_sections(tenant.id, batch_id)
    data = [SectionResponse.model_validate(s) for s in sections]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/batches/{batch_id}/sections",
    response_model=ApiResponse[SectionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Section in Batch",
)
async def create_section(
    batch_id: uuid.UUID,
    payload: SectionCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[SectionResponse]:
    service = AcademicService(session)
    created = await service.create_section(
        institution_id=tenant.id,
        batch_id=batch_id,
        name=payload.name,
        capacity=payload.capacity,
        actor_user_id=caller.id,
    )
    return build_response(data=SectionResponse.model_validate(created), request=request)


# =========================================================================
# COURSES & OFFERINGS
# =========================================================================
@router.get(
    "/courses",
    response_model=ApiResponse[List[CourseResponse]],
    summary="List Catalog Courses",
)
async def list_courses(
    request: Request,
    department_id: Optional[uuid.UUID] = Query(None, description="Filter by department"),
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[CourseResponse]]:
    service = AcademicService(session)
    courses = await service.list_courses(tenant.id, department_id=department_id)
    data = [CourseResponse.model_validate(c) for c in courses]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/courses",
    response_model=ApiResponse[CourseResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Catalog Course",
)
async def create_course(
    payload: CourseCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CourseResponse]:
    service = AcademicService(session)
    created = await service.create_course(
        institution_id=tenant.id,
        department_id=payload.department_id,
        code=payload.code,
        title=payload.title,
        credits=payload.credits,
        course_type=payload.course_type,
        course_metadata=payload.course_metadata,
        actor_user_id=caller.id,
    )
    return build_response(data=CourseResponse.model_validate(created), request=request)


@router.get(
    "/offerings",
    response_model=ApiResponse[List[CourseOfferingResponse]],
    summary="List Course Offerings",
)
async def list_course_offerings(
    request: Request,
    semester_id: Optional[uuid.UUID] = Query(None, description="Filter by semester"),
    tenant: Institution = Depends(get_current_tenant),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[CourseOfferingResponse]]:
    service = AcademicService(session)
    offerings = await service.list_course_offerings(tenant.id, semester_id=semester_id)
    data = [CourseOfferingResponse.model_validate(o) for o in offerings]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/offerings",
    response_model=ApiResponse[CourseOfferingResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Course Offering",
)
async def create_course_offering(
    payload: CourseOfferingCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CourseOfferingResponse]:
    service = AcademicService(session)
    created = await service.create_course_offering(
        institution_id=tenant.id,
        course_id=payload.course_id,
        academic_year_id=payload.academic_year_id,
        semester_id=payload.semester_id,
        section_id=payload.section_id,
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
        actor_user_id=caller.id,
    )
    return build_response(data=CourseOfferingResponse.model_validate(created), request=request)


# =========================================================================
# TEACHING ASSIGNMENTS & ENROLLMENTS
# =========================================================================
@router.post(
    "/offerings/{offering_id}/assign-faculty",
    response_model=ApiResponse[TeachingAssignmentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Assign Faculty to Course Offering",
)
async def assign_faculty(
    offering_id: uuid.UUID,
    payload: TeachingAssignmentCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[TeachingAssignmentResponse]:
    service = AcademicService(session)
    created = await service.assign_faculty(
        institution_id=tenant.id,
        course_offering_id=offering_id,
        faculty_user_id=payload.faculty_user_id,
        role_type=payload.role_type,
        actor_user_id=caller.id,
    )
    return build_response(data=TeachingAssignmentResponse.model_validate(created), request=request)


@router.post(
    "/offerings/{offering_id}/enroll",
    response_model=ApiResponse[StudentEnrollmentResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Enroll Student in Course Offering",
)
async def enroll_student(
    offering_id: uuid.UUID,
    payload: StudentEnrollmentCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[StudentEnrollmentResponse]:
    service = AcademicService(session)
    created = await service.enroll_student(
        institution_id=tenant.id,
        course_offering_id=offering_id,
        student_user_id=payload.student_user_id,
        actor_user_id=caller.id,
    )
    return build_response(data=StudentEnrollmentResponse.model_validate(created), request=request)


@router.get(
    "/offerings/{offering_id}/enrollments",
    response_model=ApiResponse[List[StudentEnrollmentResponse]],
    summary="List Enrolled Students for Offering",
)
async def list_offering_enrollments(
    offering_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    caller: User = Depends(
        require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD, SystemRole.FACULTY)
    ),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[StudentEnrollmentResponse]]:
    service = AcademicService(session)
    enrollments = await service.list_offering_enrollments(tenant.id, offering_id)
    data = [StudentEnrollmentResponse.model_validate(e) for e in enrollments]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)
