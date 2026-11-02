"""Dhruva.AI V2 — Colleges & Higher Education Institution API Routes."""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.domain.identity.models import User
from src.domain.identity.roles import SystemRole
from src.domain.college.models import College, CollegeRequest
from src.domain.academic.models import StudentProfile
from src.infrastructure.persistence.postgres.database import get_db_session
from src.infrastructure.repositories.college_repository import CollegeRepository
from src.interfaces.http.dependencies import (
    build_response,
    get_current_user,
    require_roles,
)
from src.interfaces.http.schemas.college import (
    CollegeAnalyticsItem,
    CollegeCreateRequest,
    CollegeRequestAction,
    CollegeRequestResponse,
    CollegeResponse,
    CollegeSubmitRequest,
    CollegeUpdateRequest,
    UpdateUserCollegeRequest,
)
from src.interfaces.http.schemas.envelope import ApiResponse

router = APIRouter(prefix="", tags=["Colleges"])


@router.get(
    "/colleges",
    response_model=ApiResponse[List[CollegeResponse]],
    summary="List Accredited Colleges",
)
async def list_colleges(
    request: Request,
    district: Optional[str] = Query(None, description="Filter by district, e.g. Coimbatore"),
    type: Optional[str] = Query(None, alias="type", description="Filter by institution type"),
    q: Optional[str] = Query(None, description="Search term for name or keyword"),
    status: str = Query("ACTIVE", description="College status filter"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[CollegeResponse]]:
    """Retrieve directory of higher education institutions with search and category filters."""
    repo = CollegeRepository(session)
    skip = (page - 1) * page_size
    colleges = await repo.list_colleges(
        district=district,
        institution_type=type,
        search=q,
        status=status,
        skip=skip,
        limit=page_size,
    )
    data = [CollegeResponse.model_validate(c) for c in colleges]
    return build_response(data=data, request=request)


@router.get(
    "/colleges/search",
    response_model=ApiResponse[List[CollegeResponse]],
    summary="Search Colleges Autocomplete",
)
async def search_colleges(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query string"),
    district: Optional[str] = Query(None, description="Optional district filter"),
    limit: int = Query(30, ge=1, le=100),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[CollegeResponse]]:
    """Instant search-as-you-type endpoint for college selection dropdowns."""
    repo = CollegeRepository(session)
    results = await repo.search_colleges(query=q, district=district, limit=limit)
    data = [CollegeResponse.model_validate(c) for c in results]
    return build_response(data=data, request=request)


@router.get(
    "/colleges/{college_id}",
    response_model=ApiResponse[CollegeResponse],
    summary="Get College Details",
)
async def get_college(
    college_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CollegeResponse]:
    """Retrieve detailed profile of a specific higher education institution."""
    repo = CollegeRepository(session)
    college = await repo.get_by_id(college_id)
    if not college:
        raise NotFoundError("College not found", identifier=str(college_id))
    return build_response(data=CollegeResponse.model_validate(college), request=request)


@router.post(
    "/colleges/request",
    response_model=ApiResponse[CollegeRequestResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit Unlisted College Addition Request",
)
async def submit_college_request(
    payload: CollegeSubmitRequest,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CollegeRequestResponse]:
    """Submit request to add an institution not currently listed in the directory."""
    repo = CollegeRepository(session)

    # Check if college already exists
    existing = await repo.get_by_name(payload.college_name)
    if existing:
        raise ConflictError(f"'{payload.college_name}' is already registered in the directory.")

    req_obj = CollegeRequest(
        id=uuid.uuid4(),
        requester_name=payload.requester_name.strip(),
        requester_email=payload.requester_email.strip().lower(),
        college_name=payload.college_name.strip(),
        institution_type=payload.institution_type,
        location=payload.location,
        status="PENDING",
    )
    created = await repo.create_request(req_obj)
    await session.commit()
    return build_response(data=CollegeRequestResponse.model_validate(created), request=request)


@router.post(
    "/colleges",
    response_model=ApiResponse[CollegeResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Add New College (Admin Only)",
)
async def create_college(
    payload: CollegeCreateRequest,
    request: Request,
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CollegeResponse]:
    """Admin-only endpoint to add a verified institution to the directory."""
    repo = CollegeRepository(session)
    existing = await repo.get_by_name(payload.name)
    if existing:
        raise ConflictError(f"College with name '{payload.name}' already exists.")

    college = College(
        id=uuid.uuid4(),
        name=payload.name.strip(),
        code=payload.code.strip() if payload.code else None,
        institution_type=payload.institution_type.strip(),
        affiliated_university=payload.affiliated_university.strip() if payload.affiliated_university else None,
        location=payload.location.strip(),
        district=payload.district.strip(),
        state=payload.state.strip(),
        website=payload.website.strip() if payload.website else None,
        accreditation=payload.accreditation.strip() if payload.accreditation else None,
        status=payload.status.strip().upper(),
    )
    created = await repo.create(college)
    await session.commit()
    return build_response(data=CollegeResponse.model_validate(created), request=request)


@router.put(
    "/colleges/{college_id}",
    response_model=ApiResponse[CollegeResponse],
    summary="Update College Details (Admin Only)",
)
async def update_college(
    college_id: uuid.UUID,
    payload: CollegeUpdateRequest,
    request: Request,
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CollegeResponse]:
    """Admin-only endpoint to edit institution details or change active status."""
    repo = CollegeRepository(session)
    college = await repo.get_by_id(college_id)
    if not college:
        raise NotFoundError("College not found", identifier=str(college_id))

    updates = payload.model_dump(exclude_unset=True)
    updated = await repo.update(college, updates)
    await session.commit()
    return build_response(data=CollegeResponse.model_validate(updated), request=request)


@router.get(
    "/admin/college-requests",
    response_model=ApiResponse[List[CollegeRequestResponse]],
    summary="List User College Addition Requests (Admin Only)",
)
async def list_college_requests(
    request: Request,
    status: Optional[str] = Query(None, description="Filter: PENDING, APPROVED, REJECTED, or ALL"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[CollegeRequestResponse]]:
    """Administrative review queue for user-submitted college requests."""
    repo = CollegeRepository(session)
    skip = (page - 1) * page_size
    requests_list = await repo.list_requests(status=status, skip=skip, limit=page_size)
    data = [CollegeRequestResponse.model_validate(r) for r in requests_list]
    return build_response(data=data, request=request)


@router.post(
    "/admin/college-requests/{request_id}/approve",
    response_model=ApiResponse[CollegeResponse],
    summary="Approve College Addition Request (Admin Only)",
)
async def approve_college_request(
    request_id: uuid.UUID,
    request: Request,
    action: Optional[CollegeRequestAction] = None,
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CollegeResponse]:
    """Approve user submission, automatically provision the college, and mark request approved."""
    repo = CollegeRepository(session)
    req_obj = await repo.get_request_by_id(request_id)
    if not req_obj:
        raise NotFoundError("College request not found", identifier=str(request_id))

    # Check if college already exists
    existing = await repo.get_by_name(req_obj.college_name)
    if existing:
        req_obj.status = "APPROVED"
        req_obj.admin_notes = action.admin_notes if action else "Already registered"
        await session.commit()
        return build_response(data=CollegeResponse.model_validate(existing), request=request)

    # Create the new college
    new_col = College(
        id=uuid.uuid4(),
        name=req_obj.college_name.strip(),
        institution_type=req_obj.institution_type or "Higher Education Institution",
        location=req_obj.location or "Coimbatore",
        district="Coimbatore",
        state="Tamil Nadu",
        status="ACTIVE",
    )
    created = await repo.create(new_col)

    # Mark request approved
    req_obj.status = "APPROVED"
    if action and action.admin_notes:
        req_obj.admin_notes = action.admin_notes.strip()

    await session.commit()
    return build_response(data=CollegeResponse.model_validate(created), request=request)


@router.post(
    "/admin/college-requests/{request_id}/reject",
    response_model=ApiResponse[CollegeRequestResponse],
    summary="Reject College Addition Request (Admin Only)",
)
async def reject_college_request(
    request_id: uuid.UUID,
    request: Request,
    action: CollegeRequestAction,
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[CollegeRequestResponse]:
    """Reject an unverified or duplicate user college submission."""
    repo = CollegeRepository(session)
    req_obj = await repo.get_request_by_id(request_id)
    if not req_obj:
        raise NotFoundError("College request not found", identifier=str(request_id))

    req_obj.status = "REJECTED"
    req_obj.admin_notes = action.admin_notes.strip() if action.admin_notes else "Not approved"
    await session.commit()
    return build_response(data=CollegeRequestResponse.model_validate(req_obj), request=request)


@router.get(
    "/analytics/college-wise",
    response_model=ApiResponse[List[CollegeAnalyticsItem]],
    summary="College-Wise Institutional Analytics",
)
async def get_college_wise_analytics(
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[CollegeAnalyticsItem]]:
    """Retrieve college-level breakdown of student enrollment and performance benchmarks."""
    repo = CollegeRepository(session)
    data = await repo.get_college_wise_analytics()
    return build_response(data=data, request=request)


@router.put(
    "/auth/profile/college",
    response_model=ApiResponse[dict],
    summary="Update Authenticated User's College",
)
async def update_user_college(
    payload: UpdateUserCollegeRequest,
    request: Request,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[dict]:
    """Associate or update the authenticated user's selected higher education institution."""
    repo = CollegeRepository(session)
    college = await repo.get_by_id(payload.college_id)
    if not college:
        raise NotFoundError("Selected college not found", identifier=str(payload.college_id))

    # Update user record
    user.college_id = college.id

    # If student, also update student profile
    from sqlalchemy import select
    stud_stmt = select(StudentProfile).where(StudentProfile.user_id == user.id)
    stud_profile = (await session.execute(stud_stmt)).scalar_one_or_none()
    if stud_profile:
        stud_profile.college_id = college.id

    await session.commit()
    return build_response(
        data={
            "message": f"College successfully updated to {college.name}",
            "college_id": str(college.id),
            "college_name": college.name,
            "college_location": college.location,
            "district": college.district,
        },
        request=request,
    )
