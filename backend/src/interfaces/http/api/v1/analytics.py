"""Dhruva.AI V2 — Interventions, Notification Hub & Institutional Analytics API Endpoints.

Prefix: /institutions/{institution_slug}/...
Enforces:
- Strict multi-tenant isolation.
- Recipient-isolated notification operations.
- Deterministic early-warning risk threshold evaluation.
- Pre-computed rollup caching with live fallback.
"""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.analytics.analytics_service import AnalyticsService
from src.application.analytics.notification_service import NotificationService
from src.domain.identity.models import Institution, User
from src.domain.identity.roles import SystemRole
from src.infrastructure.persistence.postgres.database import get_db_session
from src.interfaces.http.dependencies import (
    build_response,
    get_current_tenant,
    get_current_user,
    require_roles,
)
from src.interfaces.http.schemas.analytics import (
    AnalyticsRollupResponse,
    AtRiskStudentResponse,
    InterventionCreateRequest,
    InterventionResponse,
    InterventionUpdateRequest,
    NotificationBatchReadResponse,
    NotificationResponse,
)
from src.interfaces.http.schemas.envelope import ApiResponse, PaginationMeta

router = APIRouter(prefix="/institutions/{institution_slug}", tags=["Interventions, Notifications & Analytics"])


# =============================================================================
# 1. INTERVENTIONS WORKSPACE
# =============================================================================

@router.post(
    "/interventions",
    response_model=ApiResponse[InterventionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create Academic Intervention",
)
async def create_intervention(
    request: Request,
    payload: InterventionCreateRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(
        SystemRole.SUPER_ADMIN,
        SystemRole.INSTITUTION_ADMIN,
        SystemRole.HOD,
        SystemRole.FACULTY,
    )),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[InterventionResponse]:
    analytics_service = AnalyticsService(db)
    intervention = await analytics_service.create_intervention(
        institution_id=tenant.id,
        student_user_id=payload.student_user_id,
        faculty_user_id=payload.faculty_user_id or user.id,
        intervention_type=payload.intervention_type,
        trigger_reason=payload.trigger_reason,
        action_plan=payload.action_plan,
        notes=payload.notes,
        due_date=payload.due_date,
    )
    return build_response(
        data=InterventionResponse.model_validate(intervention),
        request=request,
    )


@router.get(
    "/interventions",
    response_model=ApiResponse[List[InterventionResponse]],
    summary="List Academic Interventions",
)
async def list_interventions(
    request: Request,
    student_user_id: Optional[uuid.UUID] = Query(None),
    faculty_user_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[InterventionResponse]]:
    # If the user is a student, enforce self-query isolation
    effective_student_id = student_user_id
    if SystemRole.STUDENT.value in user.roles:
        effective_student_id = user.id

    analytics_service = AnalyticsService(db)
    interventions = await analytics_service.list_interventions(
        institution_id=tenant.id,
        student_user_id=effective_student_id,
        faculty_user_id=faculty_user_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return build_response(
        data=[InterventionResponse.model_validate(i) for i in interventions],
        request=request,
        pagination=PaginationMeta(total=len(interventions), page=1, page_size=limit),
    )


@router.patch(
    "/interventions/{intervention_id}",
    response_model=ApiResponse[InterventionResponse],
    summary="Update Academic Intervention",
)
async def update_intervention(
    request: Request,
    intervention_id: uuid.UUID,
    payload: InterventionUpdateRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(
        SystemRole.SUPER_ADMIN,
        SystemRole.INSTITUTION_ADMIN,
        SystemRole.HOD,
        SystemRole.FACULTY,
    )),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[InterventionResponse]:
    analytics_service = AnalyticsService(db)
    intervention = await analytics_service.update_intervention_status(
        institution_id=tenant.id,
        intervention_id=intervention_id,
        user_id=user.id,
        status=payload.status or "IN_PROGRESS",
        outcome_notes=payload.outcome_notes,
        action_plan=payload.action_plan,
    )
    return build_response(
        data=InterventionResponse.model_validate(intervention),
        request=request,
    )


@router.post(
    "/interventions/detect-at-risk",
    response_model=ApiResponse[List[AtRiskStudentResponse]],
    summary="Detect At-Risk Students Deterministically",
)
async def detect_at_risk_students(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(
        SystemRole.SUPER_ADMIN,
        SystemRole.INSTITUTION_ADMIN,
        SystemRole.HOD,
        SystemRole.FACULTY,
    )),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[AtRiskStudentResponse]]:
    analytics_service = AnalyticsService(db)
    at_risk = await analytics_service.detect_at_risk_students(
        institution_id=tenant.id,
    )
    return build_response(
        data=[AtRiskStudentResponse(**r) for r in at_risk],
        request=request,
        pagination=PaginationMeta(total=len(at_risk), page=1, page_size=max(1, len(at_risk))),
    )


# =============================================================================
# 2. NOTIFICATION HUB
# =============================================================================

@router.get(
    "/notifications",
    response_model=ApiResponse[List[NotificationResponse]],
    summary="Get User Notifications",
)
async def get_notifications(
    request: Request,
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[NotificationResponse]]:
    notification_service = NotificationService(db)
    res = await notification_service.list_user_notifications(
        institution_id=tenant.id,
        user_id=user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )
    notifications = res["notifications"]
    return build_response(
        data=[NotificationResponse.model_validate(n) for n in notifications],
        request=request,
        pagination=PaginationMeta(total=res["total_records"], page=1, page_size=limit),
    )


@router.get(
    "/notifications/unread-count",
    response_model=ApiResponse[Dict[str, int]],
    summary="Get Unread Notification Count",
)
async def get_unread_count(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[Dict[str, int]]:
    notification_service = NotificationService(db)
    res = await notification_service.list_user_notifications(
        institution_id=tenant.id,
        user_id=user.id,
        unread_only=True,
    )
    return build_response(
        data={"unread_count": res["unread_count"]},
        request=request,
    )


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=ApiResponse[NotificationResponse],
    summary="Mark Notification As Read",
)
async def mark_notification_read(
    request: Request,
    notification_id: uuid.UUID,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[NotificationResponse]:
    notification_service = NotificationService(db)
    notification = await notification_service.mark_as_read(
        institution_id=tenant.id,
        notification_id=notification_id,
        user_id=user.id,
    )
    return build_response(
        data=NotificationResponse.model_validate(notification),
        request=request,
    )


@router.post(
    "/notifications/read-all",
    response_model=ApiResponse[NotificationBatchReadResponse],
    summary="Mark All Notifications As Read",
)
async def mark_all_notifications_read(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[NotificationBatchReadResponse]:
    notification_service = NotificationService(db)
    count = await notification_service.mark_all_as_read(
        institution_id=tenant.id,
        user_id=user.id,
    )
    return build_response(
        data=NotificationBatchReadResponse(updated_count=count),
        request=request,
    )


# =============================================================================
# 3. INSTITUTIONAL & DEPARTMENTAL ANALYTICS
# =============================================================================

@router.get(
    "/analytics/institutional",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get Institutional Analytics Rollup",
)
async def get_institutional_analytics(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(
        SystemRole.SUPER_ADMIN,
        SystemRole.INSTITUTION_ADMIN,
        SystemRole.HOD,
        SystemRole.FACULTY,
    )),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[Dict[str, Any]]:
    analytics_service = AnalyticsService(db)
    data = await analytics_service.get_institutional_analytics(institution_id=tenant.id)
    return build_response(
        data=data,
        request=request,
    )


@router.get(
    "/analytics/departmental/{department_id}",
    response_model=ApiResponse[Dict[str, Any]],
    summary="Get Departmental Analytics Rollup",
)
async def get_departmental_analytics(
    request: Request,
    department_id: uuid.UUID,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(
        SystemRole.SUPER_ADMIN,
        SystemRole.INSTITUTION_ADMIN,
        SystemRole.HOD,
        SystemRole.FACULTY,
    )),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[Dict[str, Any]]:
    analytics_service = AnalyticsService(db)
    data = await analytics_service.get_departmental_analytics(
        institution_id=tenant.id,
        department_id=department_id,
    )
    return build_response(
        data=data,
        request=request,
    )


@router.post(
    "/analytics/compute-rollups",
    response_model=ApiResponse[Dict[str, Any]],
    status_code=status.HTTP_201_CREATED,
    summary="Compute & Cache Analytics Rollup",
)
async def compute_rollups(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(
        SystemRole.SUPER_ADMIN,
        SystemRole.INSTITUTION_ADMIN,
        SystemRole.HOD,
    )),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[Dict[str, Any]]:
    analytics_service = AnalyticsService(db)
    rollup = await analytics_service.compute_institutional_rollups(institution_id=tenant.id)
    return build_response(
        data={
            "id": str(rollup.id),
            "institution_id": str(rollup.institution_id),
            "rollup_type": rollup.rollup_type,
            "computed_at": rollup.computed_at.isoformat(),
            "metrics": rollup.metrics_payload,
        },
        request=request,
    )
