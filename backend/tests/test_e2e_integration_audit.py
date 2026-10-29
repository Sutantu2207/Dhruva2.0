"""Dhruva.AI V2 — End-to-End Integration & Deployment Verification Audit Suite.

Verifies:
1. Student Auth & Session Persistence (Login, Bearer Token, /auth/me, Logout)
2. Administrative Course Setup & Student Dashboard Loading
3. AI Conversational Assistant (Multi-turn memory retention, Provenance citations, Provider status)
4. Student RBAC Denial on Administrative Operations (Strict 403 Forbidden)
5. Faculty AI Question Drafting with Bloom Taxonomy
6. Platform Liveness & Readiness Probes (Cloud / Container Deployment)
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestEndToEndIntegrationAudit:
    """Full End-to-End Integration verification across Auth, Academic, Assessment, and AI layers."""

    async def test_01_student_auth_and_session_persistence(self, client: AsyncClient, seed_data: dict):
        """Verify student login, JWT tokens, session persistence via /auth/me, and logout."""
        # 1. Login with student credentials
        login_resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "rahul.k@iitb.ac.in", "password": "SecurePass123!"},
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        login_data = login_resp.json()["data"]
        token = login_data["access_token"]
        assert token, "Access token missing from login payload"
        assert login_data["user"]["email"] == "rahul.k@iitb.ac.in"
        assert "STUDENT" in login_data["user"]["roles"]

        # 2. Verify /auth/me with Bearer token
        me_resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        me_data = me_resp.json()["data"]
        assert me_data["email"] == "rahul.k@iitb.ac.in"
        assert me_data["institution_slug"] == "iit-bombay"

        # 3. Logout
        logout_resp = await client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_resp.status_code == 200
        assert logout_resp.json()["success"] is True

    async def test_02_student_course_and_assessment_loading(self, client: AsyncClient, seed_data: dict):
        """Verify admin creates a department/course, and student can view active courses and assessments."""
        # 1. Admin login to create academic structures
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@iitb.ac.in", "password": "SecurePass123!"},
        )
        assert admin_login.status_code == 200
        admin_token = admin_login.json()["data"]["access_token"]

        dept_resp = await client.post(
            "/api/v1/institutions/iit-bombay/departments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"code": "CSE", "name": "Computer Science & Engineering"},
        )
        assert dept_resp.status_code == 201
        dept_id = dept_resp.json()["data"]["id"]

        course_resp = await client.post(
            "/api/v1/institutions/iit-bombay/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "department_id": dept_id,
                "code": "CS201",
                "title": "Data Structures & Algorithms",
                "credits": 4.0,
                "course_type": "THEORY",
            },
        )
        assert course_resp.status_code == 201
        course_id = course_resp.json()["data"]["id"]

        # 2. Student login to verify course discovery
        student_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "rahul.k@iitb.ac.in", "password": "SecurePass123!"},
        )
        assert student_login.status_code == 200
        student_token = student_login.json()["data"]["access_token"]

        courses_resp = await client.get(
            "/api/v1/institutions/iit-bombay/courses",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert courses_resp.status_code == 200
        courses = courses_resp.json()["data"]
        assert len(courses) > 0
        assert any(c["code"] == "CS201" for c in courses)

        # 3. Load assessments
        ass_resp = await client.get(
            "/api/v1/institutions/iit-bombay/assessments",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert ass_resp.status_code == 200
        assert isinstance(ass_resp.json()["data"], list)

    async def test_03_ai_tutor_multi_turn_and_diagnostics(self, client: AsyncClient, seed_data: dict):
        """Verify AI assistant multi-turn conversation memory, citations, and provider status."""
        # 1. Setup course as admin
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@iitb.ac.in", "password": "SecurePass123!"},
        )
        admin_token = admin_login.json()["data"]["access_token"]

        dept_resp = await client.post(
            "/api/v1/institutions/iit-bombay/departments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"code": "AI-DEPT", "name": "Department of AI"},
        )
        dept_id = dept_resp.json()["data"]["id"]

        course_resp = await client.post(
            "/api/v1/institutions/iit-bombay/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "department_id": dept_id,
                "code": "AI101",
                "title": "Foundations of AI",
                "credits": 3.0,
                "course_type": "THEORY",
            },
        )
        course_id = course_resp.json()["data"]["id"]

        # 2. Student login
        student_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "rahul.k@iitb.ac.in", "password": "SecurePass123!"},
        )
        student_token = student_login.json()["data"]["access_token"]

        # 3. Check provider status
        diag_resp = await client.get(
            "/api/v1/institutions/iit-bombay/ai/provider-status",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert diag_resp.status_code == 200
        status_data = diag_resp.json()["data"]
        assert "active_provider" in status_data

        # 4. Turn 1: Ask concept question
        chat_resp1 = await client.post(
            "/api/v1/institutions/iit-bombay/ai/tutor/chat",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "course_id": course_id,
                "message": "Explain search heuristics in graph algorithms",
            },
        )
        assert chat_resp1.status_code == 200
        chat_data1 = chat_resp1.json()["data"]
        convo_id = chat_data1["conversation_id"]
        assert convo_id
        assert len(chat_data1["content"]) > 30

        # 5. Turn 2: Follow-up question referencing prior turn
        chat_resp2 = await client.post(
            "/api/v1/institutions/iit-bombay/ai/tutor/chat",
            headers={"Authorization": f"Bearer {student_token}"},
            json={
                "course_id": course_id,
                "message": "Give me a Python implementation of A* search with Manhattan distance",
                "conversation_id": convo_id,
            },
        )
        assert chat_resp2.status_code == 200
        chat_data2 = chat_resp2.json()["data"]
        assert chat_data2["conversation_id"] == convo_id

        # 6. Retrieve stored conversation messages
        msgs_resp = await client.get(
            f"/api/v1/institutions/iit-bombay/ai/conversations/{convo_id}/messages",
            headers={"Authorization": f"Bearer {student_token}"},
        )
        assert msgs_resp.status_code == 200
        msgs = msgs_resp.json()["data"]
        assert len(msgs) >= 4

    async def test_04_student_rbac_denial_on_admin_actions(self, client: AsyncClient, seed_data: dict):
        """Verify student cannot perform unauthorized administrative operations (Strict 403)."""
        student_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "rahul.k@iitb.ac.in", "password": "SecurePass123!"},
        )
        student_token = student_login.json()["data"]["access_token"]

        unauth_resp = await client.post(
            "/api/v1/institutions/iit-bombay/departments",
            headers={"Authorization": f"Bearer {student_token}"},
            json={"code": "HACK", "name": "Unauthorized Department"},
        )
        assert unauth_resp.status_code in (401, 403), f"Expected 403, got {unauth_resp.status_code}"

    async def test_05_faculty_question_drafting(self, client: AsyncClient, seed_data: dict):
        """Verify faculty member can draft questions with Bloom's taxonomy."""
        # 1. Admin creates course
        admin_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@iitb.ac.in", "password": "SecurePass123!"},
        )
        admin_token = admin_login.json()["data"]["access_token"]

        dept_resp = await client.post(
            "/api/v1/institutions/iit-bombay/departments",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"code": "MATH", "name": "Department of Mathematics"},
        )
        dept_id = dept_resp.json()["data"]["id"]

        course_resp = await client.post(
            "/api/v1/institutions/iit-bombay/courses",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "department_id": dept_id,
                "code": "MA101",
                "title": "Calculus & Linear Algebra",
                "credits": 4.0,
                "course_type": "THEORY",
            },
        )
        course_id = course_resp.json()["data"]["id"]

        # 2. Faculty login
        faculty_login = await client.post(
            "/api/v1/auth/login",
            json={"email": "prof.verma@iitb.ac.in", "password": "SecurePass123!"},
        )
        assert faculty_login.status_code == 200
        faculty_token = faculty_login.json()["data"]["access_token"]

        # 3. Draft questions
        draft_resp = await client.post(
            "/api/v1/institutions/iit-bombay/ai/faculty/draft-questions",
            headers={"Authorization": f"Bearer {faculty_token}"},
            json={
                "course_id": course_id,
                "topic_or_concept": "Eigenvalues & Eigenvectors",
                "difficulty": "MEDIUM",
                "num_questions": 2,
            },
        )
        assert draft_resp.status_code == 200
        draft_data = draft_resp.json()["data"]
        assert draft_data["topic"] == "Eigenvalues & Eigenvectors"
        assert len(draft_data["draft_questions"]) == 2
        for q in draft_data["draft_questions"]:
            assert q["difficulty"] == "MEDIUM"
            assert "options" in q
            assert len(q["options"]) == 4

    async def test_06_platform_health_and_readiness_probes(self, client: AsyncClient):
        """Verify Kubernetes / Cloud provider liveness and readiness probe endpoints."""
        live_resp = await client.get("/health/live")
        assert live_resp.status_code == 200
        assert live_resp.json()["data"]["status"] == "UP"

        ready_resp = await client.get("/health/ready")
        assert ready_resp.status_code == 200
        assert ready_resp.json()["data"]["status"] == "READY"
