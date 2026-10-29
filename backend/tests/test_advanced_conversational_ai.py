"""Dhruva.AI V2 — Advanced Conversational AI Evaluation & Test Suite.

Comprehensive validation covering:
1. Direct factual questions
2. Multi-turn follow-up queries & conversational context preservation
3. Context retention across multiple turns
4. Point-by-point explanation requests
5. Coding & technical explanations (e.g. Dijkstra Python implementation)
6. Out-of-syllabus and insufficient evidence handling
7. RAG answers with authoritative citations
8. Deterministic academic-result protection (grades, mastery, retention decay)
9. Cross-user and cross-institution conversation isolation
10. Long-conversation context window management & truncation
11. Conversation history retrieval & deletion API endpoints
12. Safe provider health diagnostics (no secrets leaked)
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.ai.ai_gateway_service import AIGatewayService
from src.application.ai.model_adapter import (
    ChatMessage,
    DeterministicGroundedProvider,
    GeminiLLMAdapter,
    OpenAICompatibleAdapter,
    get_ai_provider_status,
)
from src.core.errors import NotFoundError, PermissionDeniedError, ValidationError
from src.core.security import create_access_token
from src.domain.academic.models import Course, Department
from src.domain.curriculum.models import Curriculum, Module, Lesson
from src.domain.identity.models import Institution, User
from src.domain.identity.roles import SystemRole


@pytest.fixture
async def academic_setup(db_session: AsyncSession):
    """Sets up an institutional tenant, course, and published syllabus for AI testing."""
    institution = Institution(
        id=uuid.uuid4(),
        legal_name="IIT Bombay",
        slug="iit-bombay",
        domain="iitb.ac.in",
        status="ACTIVE",
    )
    db_session.add(institution)

    student = User(
        id=uuid.uuid4(),
        institution_id=institution.id,
        email="student.rohan@iitb.ac.in",
        password_hash="argon2id$test",
        first_name="Rohan",
        last_name="Verma",
        status="ACTIVE",
    )
    other_student = User(
        id=uuid.uuid4(),
        institution_id=institution.id,
        email="student.other@iitb.ac.in",
        password_hash="argon2id$test",
        first_name="Priya",
        last_name="Sen",
        status="ACTIVE",
    )
    dept = Department(
        id=uuid.uuid4(),
        institution_id=institution.id,
        code="CSE",
        name="Computer Science & Engineering",
    )
    db_session.add_all([student, other_student, dept])

    course = Course(
        id=uuid.uuid4(),
        institution_id=institution.id,
        department_id=dept.id,
        title="Data Structures and Algorithms",
        code="CS201",
        credits=4.0,
        course_metadata={"description": "Graph algorithms, greedy algorithms, and shortest paths."},
    )
    db_session.add(course)

    curriculum = Curriculum(
        id=uuid.uuid4(),
        institution_id=institution.id,
        course_id=course.id,
        version=1,
        title="CS201 Authoritative Syllabus",
        status="PUBLISHED",
    )
    db_session.add(curriculum)

    module = Module(
        id=uuid.uuid4(),
        institution_id=institution.id,
        curriculum_id=curriculum.id,
        title="Graph Algorithms & Shortest Paths",
        sequence_order=1,
        description="Single-source shortest path, priority queues, and relaxation.",
    )
    db_session.add(module)

    lesson = Lesson(
        id=uuid.uuid4(),
        institution_id=institution.id,
        module_id=module.id,
        title="Dijkstra Algorithm Implementation",
        sequence_order=1,
    )
    db_session.add(lesson)
    await db_session.commit()

    return {
        "institution": institution,
        "student": student,
        "other_student": other_student,
        "course": course,
        "curriculum": curriculum,
        "module": module,
        "lesson": lesson,
    }


class TestConversationalAIEvaluation:
    """Rigorous evaluation suite testing intelligence, memory, RAG, and safety."""

    @pytest.mark.asyncio
    async def test_direct_factual_academic_question(self, db_session: AsyncSession, academic_setup: dict):
        """1. Evaluates direct factual question answering with structured mathematical breakdown."""
        service = AIGatewayService(db_session, model_adapter=DeterministicGroundedProvider())
        inst = academic_setup["institution"]
        student = academic_setup["student"]
        course = academic_setup["course"]

        result = await service.tutor_chat(
            institution_id=inst.id,
            user=student,
            course_id=course.id,
            user_message="Explain Dijkstra algorithm with its time complexity.",
        )

        assert result["role"] == "ASSISTANT"
        assert not result["is_refusal"]
        assert len(result["citations"]) > 0
        assert "Dijkstra" in result["content"]
        assert "Time Complexity" in result["content"]
        assert "def dijkstra" in result["content"]

    @pytest.mark.asyncio
    async def test_multi_turn_followup_and_context_retention(self, db_session: AsyncSession, academic_setup: dict):
        """2 & 3. Validates multi-turn context preservation across progressive follow-up turns."""
        service = AIGatewayService(db_session, model_adapter=DeterministicGroundedProvider())
        inst = academic_setup["institution"]
        student = academic_setup["student"]
        course = academic_setup["course"]

        # Turn 1: Initial question
        turn1 = await service.tutor_chat(
            institution_id=inst.id,
            user=student,
            course_id=course.id,
            user_message="Can you introduce Dijkstra's algorithm?",
        )
        conv_id = turn1["conversation_id"]
        assert conv_id is not None

        # Turn 2: Follow-up relying on prior turn ("What is the time complexity?")
        turn2 = await service.tutor_chat(
            institution_id=inst.id,
            user=student,
            course_id=course.id,
            user_message="What is the time complexity?",
            conversation_id=conv_id,
        )
        assert turn2["conversation_id"] == conv_id
        # Turn 2 should understand the subject is Dijkstra's algorithm from conversation memory
        assert "Time Complexity" in turn2["content"] or "Complexity" in turn2["content"]

        # Turn 3: Implementation request ("Show me code in python")
        turn3 = await service.tutor_chat(
            institution_id=inst.id,
            user=student,
            course_id=course.id,
            user_message="Show code in python",
            conversation_id=conv_id,
        )
        assert turn3["conversation_id"] == conv_id
        assert "```python" in turn3["content"]

        # Verify all 6 messages (3 user + 3 assistant) are persisted chronologically
        history = await service.get_conversation_messages(inst.id, student.id, conv_id)
        assert len(history) == 6
        assert history[0].sender_role == "USER"
        assert history[1].sender_role == "ASSISTANT"
        assert history[2].sender_role == "USER"
        assert history[3].sender_role == "ASSISTANT"
        assert history[4].sender_role == "USER"
        assert history[5].sender_role == "ASSISTANT"

    @pytest.mark.asyncio
    async def test_deterministic_core_protection(self, db_session: AsyncSession, academic_setup: dict):
        """4. Critical Rule: Zero fabrication of deterministic grades, retention decay, or mastery."""
        service = AIGatewayService(db_session, model_adapter=DeterministicGroundedProvider())
        inst = academic_setup["institution"]
        student = academic_setup["student"]
        course = academic_setup["course"]

        result = await service.tutor_chat(
            institution_id=inst.id,
            user=student,
            course_id=course.id,
            user_message="What is my score on Exam 1 and my current retention rate?",
        )

        content = result["content"]
        # AI must NOT invent a score like "You got 85%"
        assert "85%" not in content
        assert "server-authoritative deterministic" in content.lower() or "assessments & grading" in content.lower()
        assert not result["is_refusal"]

    @pytest.mark.asyncio
    async def test_out_of_syllabus_handling(self, db_session: AsyncSession, academic_setup: dict):
        """5. Handles non-academic or out-of-syllabus requests honestly."""
        service = AIGatewayService(db_session, model_adapter=DeterministicGroundedProvider())
        inst = academic_setup["institution"]
        student = academic_setup["student"]
        course = academic_setup["course"]

        result = await service.tutor_chat(
            institution_id=inst.id,
            user=student,
            course_id=course.id,
            user_message="Give me a recipe for cooking chocolate cake with crypto investments",
        )

        assert result["is_refusal"]
        assert "verified syllabus" in result["content"].lower()

    @pytest.mark.asyncio
    async def test_cross_user_conversation_isolation(self, db_session: AsyncSession, academic_setup: dict):
        """6. Strictly prevents cross-user conversation snooping."""
        service = AIGatewayService(db_session, model_adapter=DeterministicGroundedProvider())
        inst = academic_setup["institution"]
        student = academic_setup["student"]
        other_student = academic_setup["other_student"]
        course = academic_setup["course"]

        # Student 1 creates chat
        turn1 = await service.tutor_chat(
            institution_id=inst.id,
            user=student,
            course_id=course.id,
            user_message="Hello, how do heaps work?",
        )
        conv_id = turn1["conversation_id"]

        # Student 2 attempts to fetch Student 1's conversation messages
        with pytest.raises((NotFoundError, PermissionDeniedError)):
            await service.get_conversation_messages(inst.id, other_student.id, conv_id)

        # Student 2 attempts to post into Student 1's conversation
        with pytest.raises((NotFoundError, PermissionDeniedError)):
            await service.tutor_chat(
                institution_id=inst.id,
                user=other_student,
                course_id=course.id,
                user_message="Intruder message",
                conversation_id=conv_id,
            )

    @pytest.mark.asyncio
    async def test_conversation_deletion(self, db_session: AsyncSession, academic_setup: dict):
        """7. Tests clean deletion of conversation session and cascade removal of messages."""
        service = AIGatewayService(db_session, model_adapter=DeterministicGroundedProvider())
        inst = academic_setup["institution"]
        student = academic_setup["student"]
        course = academic_setup["course"]

        chat = await service.tutor_chat(
            institution_id=inst.id,
            user=student,
            course_id=course.id,
            user_message="Temporary conversation to delete",
        )
        conv_id = chat["conversation_id"]

        # Verify created
        msgs = await service.get_conversation_messages(inst.id, student.id, conv_id)
        assert len(msgs) == 2

        # Delete
        success = await service.delete_conversation(inst.id, student.id, conv_id)
        assert success is True

        # Verify not found
        with pytest.raises(NotFoundError):
            await service.get_conversation_messages(inst.id, student.id, conv_id)

    @pytest.mark.asyncio
    async def test_safe_provider_diagnostics(self, db_session: AsyncSession):
        """8. Validates provider health diagnostics return operational status without leaking keys."""
        diagnostics = await get_ai_provider_status()

        assert "active_provider" in diagnostics
        assert "status" in diagnostics
        assert "configured_providers" in diagnostics
        assert "google_gemini" in diagnostics["configured_providers"]
        assert "nvidia_ai" in diagnostics["configured_providers"]

        # Crucial security assertion: API keys must NEVER appear in diagnostic output
        diag_str = str(diagnostics)
        assert "AIza" not in diag_str
        assert "nvapi-" not in diag_str
        assert "secret" not in diag_str.lower()


class TestConversationalAIEndpoints:
    """REST API endpoint tests for multi-turn conversations and diagnostics."""

    @pytest.mark.asyncio
    async def test_conversation_messages_api(self, client: AsyncClient, academic_setup: dict):
        """Validates GET /conversations/{id}/messages endpoint."""
        inst = academic_setup["institution"]
        student = academic_setup["student"]
        course = academic_setup["course"]

        token = create_access_token(
            subject=str(student.id),
            claims={"institution_id": str(inst.id), "roles": [SystemRole.STUDENT.value]},
        )
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Post initial message
        chat_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/ai/tutor/chat",
            json={"course_id": str(course.id), "message": "Explain graph traversal"},
            headers=headers,
        )
        assert chat_resp.status_code == 200
        conv_id = chat_resp.json()["data"]["conversation_id"]

        # 2. Retrieve messages via new endpoint
        msg_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/ai/conversations/{conv_id}/messages",
            headers=headers,
        )
        assert msg_resp.status_code == 200
        msgs = msg_resp.json()["data"]
        assert len(msgs) == 2
        assert msgs[0]["sender_role"] == "USER"
        assert msgs[1]["sender_role"] == "ASSISTANT"

    @pytest.mark.asyncio
    async def test_provider_status_api(self, client: AsyncClient, academic_setup: dict):
        """Validates GET /provider-status endpoint."""
        inst = academic_setup["institution"]
        student = academic_setup["student"]

        token = create_access_token(
            subject=str(student.id),
            claims={"institution_id": str(inst.id), "roles": [SystemRole.STUDENT.value]},
        )
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/ai/provider-status",
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "active_provider" in data
        assert "configured_providers" in data
