"""Dhruva.AI V2 — Guardrailed AI Gateway Application Service.

Coordinates:
- Security checks & Prompt Injection screening
- PII Sanitization & Zero data leakage
- Tenant-isolated Context Building & Provenance citations
- LLM inference & Structured output validation
- Immutable Audit Logging
"""

import hashlib
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.ai.context_builder import ContextBuilder
from src.application.ai.model_adapter import BaseLLMAdapter, DeterministicGroundedProvider
from src.application.ai.pii_sanitizer import PIISanitizer
from src.application.ai.prompt_guard import PromptGuard
from src.core.errors import NotFoundError, PermissionDeniedError, ValidationError
from src.domain.ai.models import AIAuditLog, AIConversation, AIMessage
from src.domain.identity.models import User
from src.infrastructure.persistence.postgres.base import utc_now


class AIGatewayService:
    """Core orchestration service for institutional AI workflows."""

    def __init__(self, session: AsyncSession, model_adapter: Optional[BaseLLMAdapter] = None):
        self.session = session
        self.context_builder = ContextBuilder(session)
        self.model_adapter = model_adapter or DeterministicGroundedProvider()

    @staticmethod
    def _hash_prompt(prompt: str) -> str:
        return hashlib.sha256(prompt.strip().encode("utf-8")).hexdigest()

    async def tutor_chat(
        self,
        institution_id: uuid.UUID,
        user: User,
        course_id: uuid.UUID,
        user_message: str,
        conversation_id: Optional[uuid.UUID] = None,
    ) -> Dict[str, Any]:
        """Executes student grounded AI tutoring workflow with multi-layered guardrails."""
        prompt_hash = self._hash_prompt(user_message)

        # 1. Prompt Injection Defense
        guard_result = PromptGuard.evaluate(user_message)
        if guard_result.verdict == "BLOCKED":
            # Log security block in audit trail
            audit = AIAuditLog(
                institution_id=institution_id,
                user_id=user.id,
                action="PROMPT_INJECTION_BLOCKED",
                prompt_hash=prompt_hash,
                pii_detected_count=0,
                safety_verdict="BLOCKED",
                tokens_used=0,
                cost_estimate=0.0,
                metadata_json={"reason": guard_result.reason, "risk_score": guard_result.risk_score},
            )
            self.session.add(audit)
            await self.session.commit()
            raise ValidationError(f"Prompt blocked by AI safety guardrail: {guard_result.reason}")

        # 2. PII Sanitization
        sanitization = PIISanitizer.sanitize(
            user_message,
            user_names=[user.first_name, user.last_name, user.full_name],
        )

        # 3. Tenant-Isolated Context Assembly
        grounded_context = await self.context_builder.build_course_context(
            institution_id=institution_id,
            course_id=course_id,
            user_query=sanitization.sanitized_text,
        )

        # 4. Model Inference
        llm_response = await self.model_adapter.generate_tutor_response(
            sanitized_prompt=sanitization.sanitized_text,
            course_name=grounded_context.course_name,
            course_code=grounded_context.course_code,
            context_text=grounded_context.assembled_context,
            citations=grounded_context.citations,
            is_out_of_syllabus=grounded_context.is_out_of_syllabus,
        )

        # 5. Conversation & Message Persistence
        conversation = None
        if conversation_id:
            conv_stmt = select(AIConversation).where(
                and_(
                    AIConversation.id == conversation_id,
                    AIConversation.institution_id == institution_id,
                    AIConversation.user_id == user.id,
                )
            )
            conversation = (await self.session.execute(conv_stmt)).scalar_one_or_none()

        if not conversation:
            # Create new conversation
            title_summary = " ".join(user_message.split()[:5])
            conversation = AIConversation(
                institution_id=institution_id,
                user_id=user.id,
                context_type="STUDENT_TUTOR",
                context_id=str(course_id),
                title=f"{grounded_context.course_code}: {title_summary}",
                status="ACTIVE",
            )
            self.session.add(conversation)
            await self.session.flush()

        # Add user message
        user_msg_entry = AIMessage(
            institution_id=institution_id,
            conversation_id=conversation.id,
            sender_role="USER",
            raw_content=user_message,
            sanitized_content=sanitization.sanitized_text,
            citations_json=[],
            model_name="user-input",
            token_count=len(user_message.split()),
            latency_ms=0,
        )
        self.session.add(user_msg_entry)

        # Add assistant message
        assistant_msg_entry = AIMessage(
            institution_id=institution_id,
            conversation_id=conversation.id,
            sender_role="ASSISTANT",
            raw_content=llm_response.content,
            sanitized_content=llm_response.content,
            citations_json=llm_response.citations,
            model_name=llm_response.model_name,
            token_count=llm_response.token_count,
            latency_ms=llm_response.latency_ms,
        )
        self.session.add(assistant_msg_entry)

        # 6. Immutable Audit Log
        cost_est = (llm_response.token_count / 1000) * 0.002
        audit = AIAuditLog(
            institution_id=institution_id,
            user_id=user.id,
            action="TUTOR_QUERY",
            prompt_hash=prompt_hash,
            pii_detected_count=sanitization.pii_detected_count,
            safety_verdict=guard_result.verdict,
            tokens_used=llm_response.token_count,
            cost_estimate=cost_est,
            metadata_json={
                "course_code": grounded_context.course_code,
                "citations_count": len(llm_response.citations),
                "is_refusal": llm_response.is_refusal,
                "latency_ms": llm_response.latency_ms,
            },
        )
        self.session.add(audit)
        await self.session.commit()

        return {
            "conversation_id": conversation.id,
            "message_id": assistant_msg_entry.id,
            "course_id": course_id,
            "course_code": grounded_context.course_code,
            "role": "ASSISTANT",
            "content": llm_response.content,
            "citations": llm_response.citations,
            "model_name": llm_response.model_name,
            "pii_detected_count": sanitization.pii_detected_count,
            "latency_ms": llm_response.latency_ms,
            "is_refusal": llm_response.is_refusal,
            "created_at": assistant_msg_entry.created_at,
        }

    async def draft_faculty_questions(
        self,
        institution_id: uuid.UUID,
        user: User,
        course_id: uuid.UUID,
        topic_or_concept: str,
        difficulty: str = "MEDIUM",
        num_questions: int = 3,
    ) -> Dict[str, Any]:
        """Generates grounded assessment questions for faculty with 1-click bank readiness."""
        # 1. Fetch Course with tenant isolation
        grounded_context = await self.context_builder.build_course_context(
            institution_id=institution_id,
            course_id=course_id,
            user_query=topic_or_concept,
        )

        # 2. Generate Drafts
        drafts = await self.model_adapter.generate_question_drafts(
            course_name=grounded_context.course_name,
            course_code=grounded_context.course_code,
            topic_or_concept=topic_or_concept,
            difficulty=difficulty,
            num_questions=num_questions,
            context_text=grounded_context.assembled_context,
        )

        # 3. Log Audit Entry
        audit = AIAuditLog(
            institution_id=institution_id,
            user_id=user.id,
            action="QUESTION_DRAFT",
            prompt_hash=self._hash_prompt(f"{grounded_context.course_code}:{topic_or_concept}:{difficulty}"),
            pii_detected_count=0,
            safety_verdict="PASS",
            tokens_used=len(drafts) * 80,
            cost_estimate=0.001,
            metadata_json={
                "course_code": grounded_context.course_code,
                "difficulty": difficulty,
                "questions_count": len(drafts),
            },
        )
        self.session.add(audit)
        await self.session.commit()

        return {
            "course_id": course_id,
            "course_code": grounded_context.course_code,
            "topic": topic_or_concept,
            "difficulty": difficulty,
            "draft_questions": drafts,
            "total_generated": len(drafts),
        }

    async def summarize_feedback(
        self,
        institution_id: uuid.UUID,
        user: User,
        course_id: uuid.UUID,
        feedback_submissions: List[str],
    ) -> Dict[str, Any]:
        """Summarizes student feedback while strictly sanitizing all student PII."""
        # 1. Fetch Course with tenant isolation
        grounded_context = await self.context_builder.build_course_context(
            institution_id=institution_id,
            course_id=course_id,
            user_query="feedback analysis",
        )

        # 2. Sanitize PII from all feedback items
        sanitized_feedback: List[str] = []
        total_pii_sanitized = 0
        for fb in feedback_submissions:
            res = PIISanitizer.sanitize(fb)
            sanitized_feedback.append(res.sanitized_text)
            total_pii_sanitized += res.pii_detected_count

        # 3. Summarize
        summary_res = await self.model_adapter.summarize_feedback(
            course_name=grounded_context.course_name,
            feedback_items=sanitized_feedback,
        )

        # 4. Audit Log
        audit = AIAuditLog(
            institution_id=institution_id,
            user_id=user.id,
            action="FEEDBACK_SUMMARY",
            prompt_hash=self._hash_prompt(f"{grounded_context.course_code}:feedback:{len(feedback_submissions)}"),
            pii_detected_count=total_pii_sanitized,
            safety_verdict="PASS",
            tokens_used=120,
            cost_estimate=0.001,
            metadata_json={
                "course_code": grounded_context.course_code,
                "feedback_count": len(feedback_submissions),
                "pii_sanitized": total_pii_sanitized,
            },
        )
        self.session.add(audit)
        await self.session.commit()

        return {
            "course_id": course_id,
            "course_code": grounded_context.course_code,
            "pii_sanitized_count": total_pii_sanitized,
            **summary_res,
        }

    async def list_conversations(
        self,
        institution_id: uuid.UUID,
        user_id: uuid.UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> List[AIConversation]:
        """Lists user's conversations strictly isolated to their user_id and institution."""
        stmt = (
            select(AIConversation)
            .where(
                and_(
                    AIConversation.institution_id == institution_id,
                    AIConversation.user_id == user_id,
                )
            )
            .order_by(desc(AIConversation.updated_at))
            .limit(limit)
            .offset(offset)
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def list_audit_logs(
        self,
        institution_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AIAuditLog]:
        """Lists AI audit entries within institutional boundaries."""
        stmt = (
            select(AIAuditLog)
            .where(AIAuditLog.institution_id == institution_id)
            .order_by(desc(AIAuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list((await self.session.execute(stmt)).scalars().all())
