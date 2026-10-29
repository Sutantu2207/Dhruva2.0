"""Dhruva.AI V2 — Guardrailed AI Gateway Application Service.

Coordinates:
- Security checks & Prompt Injection screening
- PII Sanitization & Zero data leakage
- Tenant-isolated Context Building & Provenance citations
- Multi-turn conversation memory retrieval & context window management
- LLM inference across Gemini / NVIDIA / Deterministic providers
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
from src.application.ai.model_adapter import (
    BaseLLMAdapter,
    ChatMessage,
    get_ai_provider_status,
    get_llm_adapter,
)
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
        self.model_adapter = model_adapter or get_llm_adapter()

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
        """Executes student grounded AI tutoring workflow with multi-layered guardrails and multi-turn memory."""
        prompt_hash = self._hash_prompt(user_message)

        # 1. Prompt Injection Defense
        guard_result = PromptGuard.evaluate(user_message)
        if guard_result.verdict == "BLOCKED":
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

        # 3. Conversation Resolution & Multi-Turn History Retrieval
        conversation: Optional[AIConversation] = None
        conversation_history: List[ChatMessage] = []

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
                # Check cross-tenant leakage attempt
                cross_stmt = select(AIConversation).where(AIConversation.id == conversation_id)
                cross_conv = (await self.session.execute(cross_stmt)).scalar_one_or_none()
                if cross_conv:
                    raise PermissionDeniedError("Cross-tenant conversation access is strictly prohibited.")
                raise NotFoundError(f"Conversation {conversation_id} not found.")

            # Load recent chronological messages for multi-turn conversational context
            msg_stmt = (
                select(AIMessage)
                .where(AIMessage.conversation_id == conversation.id)
                .order_by(AIMessage.created_at.asc())
            )
            prev_messages = list((await self.session.execute(msg_stmt)).scalars().all())

            # Convert to ChatMessage format (window to last 10 messages to avoid token blowup)
            for m in prev_messages[-10:]:
                role = "user" if m.sender_role.upper() == "USER" else "model"
                conversation_history.append(ChatMessage(role=role, content=m.sanitized_content))

        # 4. Tenant-Isolated Context Assembly
        grounded_context = await self.context_builder.build_course_context(
            institution_id=institution_id,
            course_id=course_id,
            user_query=sanitization.sanitized_text,
        )

        # 5. If conversation does not exist yet, create it now
        if not conversation:
            title_summary = " ".join(user_message.split()[:5])
            if len(title_summary) > 40:
                title_summary = title_summary[:40] + "..."
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

        # 6. Model Inference with History & Grounding
        llm_response = await self.model_adapter.generate_tutor_response(
            sanitized_prompt=sanitization.sanitized_text,
            course_name=grounded_context.course_name,
            course_code=grounded_context.course_code,
            context_text=grounded_context.assembled_context,
            citations=grounded_context.citations,
            conversation_history=conversation_history,
            user_role="STUDENT",
            is_out_of_syllabus=grounded_context.is_out_of_syllabus,
        )

        # 7. Add user message
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

        # 8. Add assistant message
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

        # Update conversation timestamp
        conversation.updated_at = utc_now()

        # 9. Immutable Audit Log
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
                "model_name": llm_response.model_name,
                "is_refusal": llm_response.is_refusal,
                "conversation_id": str(conversation.id),
                "history_turns_count": len(conversation_history),
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
        """Assists faculty in generating high-quality exam questions mapped to Bloom taxonomy."""
        grounded_context = await self.context_builder.build_course_context(
            institution_id=institution_id,
            course_id=course_id,
            user_query=topic_or_concept,
        )

        drafts = await self.model_adapter.generate_question_drafts(
            course_name=grounded_context.course_name,
            course_code=grounded_context.course_code,
            topic_or_concept=topic_or_concept,
            difficulty=difficulty,
            num_questions=num_questions,
            context_text=grounded_context.assembled_context,
        )

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
        grounded_context = await self.context_builder.build_course_context(
            institution_id=institution_id,
            course_id=course_id,
            user_query="feedback analysis",
        )

        sanitized_feedback: List[str] = []
        total_pii_sanitized = 0
        for fb in feedback_submissions:
            res = PIISanitizer.sanitize(fb)
            sanitized_feedback.append(res.sanitized_text)
            total_pii_sanitized += res.pii_detected_count

        summary_res = await self.model_adapter.summarize_feedback(
            course_name=grounded_context.course_name,
            feedback_items=sanitized_feedback,
        )

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

    async def get_conversation_messages(
        self,
        institution_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> List[AIMessage]:
        """Retrieves chronological messages for an authenticated user's conversation."""
        conv_stmt = select(AIConversation).where(
            and_(
                AIConversation.id == conversation_id,
                AIConversation.institution_id == institution_id,
                AIConversation.user_id == user_id,
            )
        )
        conversation = (await self.session.execute(conv_stmt)).scalar_one_or_none()
        if not conversation:
            # Check if exists in another tenant
            cross_stmt = select(AIConversation).where(AIConversation.id == conversation_id)
            cross_conv = (await self.session.execute(cross_stmt)).scalar_one_or_none()
            if cross_conv:
                raise PermissionDeniedError("Cross-tenant conversation access is strictly prohibited.")
            raise NotFoundError(f"Conversation {conversation_id} not found.")

        msg_stmt = (
            select(AIMessage)
            .where(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at.asc())
        )
        return list((await self.session.execute(msg_stmt)).scalars().all())

    async def delete_conversation(
        self,
        institution_id: uuid.UUID,
        user_id: uuid.UUID,
        conversation_id: uuid.UUID,
    ) -> bool:
        """Deletes a conversation session and all its messages."""
        conv_stmt = select(AIConversation).where(
            and_(
                AIConversation.id == conversation_id,
                AIConversation.institution_id == institution_id,
                AIConversation.user_id == user_id,
            )
        )
        conversation = (await self.session.execute(conv_stmt)).scalar_one_or_none()
        if not conversation:
            raise NotFoundError(f"Conversation {conversation_id} not found.")

        await self.session.delete(conversation)
        await self.session.commit()
        return True

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

    async def get_provider_diagnostics(self) -> Dict[str, Any]:
        """Returns safe provider health and configuration diagnostics without revealing secrets."""
        return await get_ai_provider_status()
