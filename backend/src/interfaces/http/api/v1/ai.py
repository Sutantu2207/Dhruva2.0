"""Dhruva.AI V2 — Guardrailed AI Gateway & Retrieval API Endpoints.

Prefix: /institutions/{institution_slug}/ai
Enforces:
- Tenant-scoped context retrieval.
- Strict PII Sanitization.
- Prompt injection screening and blocking.
- Grounded citations for all student tutoring responses.
- Staff-only access for Question Drafting and Feedback Summarization.
"""

import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ai.ai_gateway_service import AIGatewayService
from src.domain.identity.models import Institution, User
from src.domain.identity.roles import SystemRole
from src.infrastructure.persistence.postgres.database import get_db_session
from src.interfaces.http.dependencies import (
    build_response,
    get_current_tenant,
    get_current_user,
    require_roles,
)
from src.interfaces.http.schemas.ai import (
    AIAuditLogResponse,
    AIConversationResponse,
    FeedbackSummaryRequest,
    FeedbackSummaryResponse,
    QuestionDraftRequest,
    QuestionDraftResponse,
    TutorChatRequest,
    TutorChatResponse,
)
from src.interfaces.http.schemas.envelope import ApiResponse, PaginationMeta

router = APIRouter(prefix="/institutions/{institution_slug}/ai", tags=["Guardrailed AI Gateway"])


@router.post(
    "/tutor/chat",
    response_model=ApiResponse[TutorChatResponse],
    summary="Student Grounded AI Tutor Chat",
)
async def tutor_chat(
    request: Request,
    payload: TutorChatRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[TutorChatResponse]:
    """Provides grounded tutoring assistance strictly citing verified course syllabi."""
    ai_service = AIGatewayService(db)
    result = await ai_service.tutor_chat(
        institution_id=tenant.id,
        user=user,
        course_id=payload.course_id,
        user_message=payload.message,
        conversation_id=payload.conversation_id,
    )
    return build_response(
        data=TutorChatResponse.model_validate(result),
        request=request,
    )


@router.post(
    "/faculty/draft-questions",
    response_model=ApiResponse[QuestionDraftResponse],
    summary="Faculty AI Question Drafting Assistant",
)
async def draft_questions(
    request: Request,
    payload: QuestionDraftRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(
        SystemRole.SUPER_ADMIN,
        SystemRole.INSTITUTION_ADMIN,
        SystemRole.HOD,
        SystemRole.FACULTY,
    )),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[QuestionDraftResponse]:
    """Generates syllabus-grounded question drafts with bloom levels and distractor rationales."""
    ai_service = AIGatewayService(db)
    result = await ai_service.draft_faculty_questions(
        institution_id=tenant.id,
        user=user,
        course_id=payload.course_id,
        topic_or_concept=payload.topic_or_concept,
        difficulty=payload.difficulty,
        num_questions=payload.num_questions,
    )
    return build_response(
        data=QuestionDraftResponse.model_validate(result),
        request=request,
    )


@router.post(
    "/faculty/summarize-feedback",
    response_model=ApiResponse[FeedbackSummaryResponse],
    summary="Faculty Feedback Summarizer with PII Redaction",
)
async def summarize_feedback(
    request: Request,
    payload: FeedbackSummaryRequest,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(
        SystemRole.SUPER_ADMIN,
        SystemRole.INSTITUTION_ADMIN,
        SystemRole.HOD,
        SystemRole.FACULTY,
    )),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[FeedbackSummaryResponse]:
    """Analyzes and summarizes student course feedback while strictly scrubbing student PII."""
    ai_service = AIGatewayService(db)
    result = await ai_service.summarize_feedback(
        institution_id=tenant.id,
        user=user,
        course_id=payload.course_id,
        feedback_submissions=payload.feedback_items,
    )
    return build_response(
        data=FeedbackSummaryResponse.model_validate(result),
        request=request,
    )


@router.get(
    "/conversations",
    response_model=ApiResponse[List[AIConversationResponse]],
    summary="List User AI Conversations",
)
async def list_conversations(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[AIConversationResponse]]:
    """Lists current user's AI conversations within institutional boundaries."""
    ai_service = AIGatewayService(db)
    conversations = await ai_service.list_conversations(
        institution_id=tenant.id,
        user_id=user.id,
        limit=limit,
        offset=offset,
    )
    return build_response(
        data=[AIConversationResponse.model_validate(c) for c in conversations],
        request=request,
        pagination=PaginationMeta(total=len(conversations), page=1, page_size=limit),
    )


@router.get(
    "/audit-logs",
    response_model=ApiResponse[List[AIAuditLogResponse]],
    summary="List Institutional AI Audit Logs",
)
async def list_audit_logs(
    request: Request,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(
        SystemRole.SUPER_ADMIN,
        SystemRole.INSTITUTION_ADMIN,
        SystemRole.HOD,
    )),
    db: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[AIAuditLogResponse]]:
    """Administrative inspection of AI safety verdicts, prompt hashes, and telemetry."""
    ai_service = AIGatewayService(db)
    logs = await ai_service.list_audit_logs(
        institution_id=tenant.id,
        limit=limit,
        offset=offset,
    )
    return build_response(
        data=[AIAuditLogResponse.model_validate(l) for l in logs],
        request=request,
        pagination=PaginationMeta(total=len(logs), page=1, page_size=limit),
    )
