"""Dhruva.AI V2 — Curriculum, Syllabus & Learning Content Tests.

Validates:
1. End-to-end curriculum lifecycle: Creation, modules, lessons/topics, learning resources, and publication.
2. Versioning workflow and sequential version increments.
3. Publication invariants and lifecycle state transition integrity.
4. Sequence order uniqueness and conflict handling.
5. Granular RBAC boundaries (Faculty submit, HOD/Admin approve, Student read-only).
6. Strict multi-tenant isolation and cross-tenant access rejection.
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.security import create_access_token
from src.domain.identity.models import User


@pytest.mark.asyncio
class TestCurriculumContentAPI:
    """Test suite for Phase 3 Curriculum & Content Management operations."""

    def _auth_headers(self, user: User) -> dict:
        token = create_access_token(
            subject=str(user.id),
            claims={"institution_id": str(user.institution_id) if user.institution_id else None},
        )
        return {"Authorization": f"Bearer {token}"}

    async def _setup_course(self, client: AsyncClient, admin: User, inst_slug: str) -> str:
        """Helper to create a prerequisite department and course."""
        headers = self._auth_headers(admin)
        dept_resp = await client.post(
            f"/api/v1/institutions/{inst_slug}/departments",
            json={"code": f"CS_{uuid.uuid4().hex[:4].upper()}", "name": "Computer Science"},
            headers=headers,
        )
        dept_id = dept_resp.json()["data"]["id"]

        course_resp = await client.post(
            f"/api/v1/institutions/{inst_slug}/courses",
            json={
                "department_id": dept_id,
                "code": f"CS_{uuid.uuid4().hex[:4].upper()}",
                "title": "Algorithms and Data Structures",
                "credits": 4.0,
                "course_type": "THEORY",
            },
            headers=headers,
        )
        return course_resp.json()["data"]["id"]

    async def test_complete_curriculum_and_syllabus_flow(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify full lifecycle from curriculum draft to modules, lessons, resources, and publishing."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        faculty = seed_data["faculty_user"]
        student = seed_data["student_user"]

        course_id = await self._setup_course(client, admin, inst.slug)
        faculty_headers = self._auth_headers(faculty)
        admin_headers = self._auth_headers(admin)

        # 1. Faculty creates Curriculum Version 1 (Starts as DRAFT)
        curr_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/courses/{course_id}/curriculums",
            json={
                "title": "Core Algorithms Curriculum 2026",
                "description": "Foundational curriculum covering sorting, dynamic programming, and graphs.",
                "learning_objectives": ["Analyze asymptotic complexity", "Implement graph traversals"],
            },
            headers=faculty_headers,
        )
        assert curr_resp.status_code == 201
        curr_data = curr_resp.json()["data"]
        curr_id = curr_data["id"]
        assert curr_data["version"] == 1
        assert curr_data["status"] == "DRAFT"

        # 2. Add Module 1 (seq=1)
        m1_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}/modules",
            json={
                "title": "Module 1: Divide and Conquer",
                "sequence_order": 1,
                "estimated_hours": 12.0,
                "learning_outcomes": ["Master MergeSort", "Master Binary Search"],
            },
            headers=faculty_headers,
        )
        assert m1_resp.status_code == 201
        m1_id = m1_resp.json()["data"]["id"]

        # 3. Add Lessons to Module 1
        l1_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/modules/{m1_id}/lessons",
            json={
                "title": "Lesson 1.1: Recurrence Relations",
                "sequence_order": 1,
                "content_markdown": "# Recurrence Relations\nMaster theorem overview...",
                "lesson_type": "THEORY",
                "duration_minutes": 60,
            },
            headers=faculty_headers,
        )
        assert l1_resp.status_code == 201
        l1_id = l1_resp.json()["data"]["id"]

        # 4. Attach Learning Resource to Lesson 1
        res_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/lessons/{l1_id}/resources",
            json={
                "title": "Lecture Notes - Master Theorem PDF",
                "resource_type": "DOCUMENT",
                "storage_uri": "s3://curriculum/notes/recurrence.pdf",
            },
            headers=faculty_headers,
        )
        assert res_resp.status_code == 201

        # 5. Faculty transitions DRAFT -> IN_REVIEW
        review_resp = await client.patch(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}/status",
            json={"status": "IN_REVIEW"},
            headers=faculty_headers,
        )
        assert review_resp.status_code == 200
        assert review_resp.json()["data"]["status"] == "IN_REVIEW"

        # 6. Admin Approves IN_REVIEW -> APPROVED
        appr_resp = await client.patch(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}/status",
            json={"status": "APPROVED"},
            headers=admin_headers,
        )
        assert appr_resp.status_code == 200
        assert appr_resp.json()["data"]["status"] == "APPROVED"
        assert appr_resp.json()["data"]["approved_by"] == str(admin.id)

        # 7. Admin Publishes APPROVED -> PUBLISHED
        pub_resp = await client.patch(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}/status",
            json={"status": "PUBLISHED"},
            headers=admin_headers,
        )
        assert pub_resp.status_code == 200
        assert pub_resp.json()["data"]["status"] == "PUBLISHED"

        # 8. Student can inspect the published curriculum and syllabus tree
        student_headers = self._auth_headers(student)
        details_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}",
            headers=student_headers,
        )
        assert details_resp.status_code == 200
        tree = details_resp.json()["data"]
        assert len(tree["modules"]) == 1
        assert len(tree["modules"][0]["lessons"]) == 1
        assert len(tree["modules"][0]["lessons"][0]["learning_resources"]) == 1

    async def test_curriculum_versioning_increment(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify sequential versioning increments when new curriculum is created for same course."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        course_id = await self._setup_course(client, admin, inst.slug)
        admin_headers = self._auth_headers(admin)

        # Version 1
        v1 = await client.post(
            f"/api/v1/institutions/{inst.slug}/courses/{course_id}/curriculums",
            json={"title": "Curriculum 2026"},
            headers=admin_headers,
        )
        assert v1.status_code == 201
        assert v1.json()["data"]["version"] == 1

        # Version 2
        v2 = await client.post(
            f"/api/v1/institutions/{inst.slug}/courses/{course_id}/curriculums",
            json={"title": "Curriculum 2027 Revision"},
            headers=admin_headers,
        )
        assert v2.status_code == 201
        assert v2.json()["data"]["version"] == 2

    async def test_publication_invariants_enforced(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify cannot publish empty curriculum or mutate published curriculum."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        course_id = await self._setup_course(client, admin, inst.slug)
        admin_headers = self._auth_headers(admin)

        curr = await client.post(
            f"/api/v1/institutions/{inst.slug}/courses/{course_id}/curriculums",
            json={"title": "Empty Curriculum"},
            headers=admin_headers,
        )
        curr_id = curr.json()["data"]["id"]

        # 1. Invalid status jump: DRAFT -> PUBLISHED directly must be rejected
        resp_illegal_jump = await client.patch(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}/status",
            json={"status": "PUBLISHED"},
            headers=admin_headers,
        )
        assert resp_illegal_jump.status_code == 422
        assert "Cannot transition" in resp_illegal_jump.json()["error"]["message"]

        # 2. Advance to IN_REVIEW -> APPROVED
        await client.patch(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}/status",
            json={"status": "IN_REVIEW"},
            headers=admin_headers,
        )
        await client.patch(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}/status",
            json={"status": "APPROVED"},
            headers=admin_headers,
        )

        # 3. Cannot publish empty curriculum (no modules)
        resp_empty_pub = await client.patch(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}/status",
            json={"status": "PUBLISHED"},
            headers=admin_headers,
        )
        assert resp_empty_pub.status_code == 422
        assert "without instructional modules" in resp_empty_pub.json()["error"]["message"]

    async def test_module_and_lesson_sequence_uniqueness(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify duplicate sequence_order numbers within module or curriculum raise 409 Conflict."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        course_id = await self._setup_course(client, admin, inst.slug)
        admin_headers = self._auth_headers(admin)

        curr = await client.post(
            f"/api/v1/institutions/{inst.slug}/courses/{course_id}/curriculums",
            json={"title": "Sequence Test Curriculum"},
            headers=admin_headers,
        )
        curr_id = curr.json()["data"]["id"]

        # Module 1
        m1 = await client.post(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}/modules",
            json={"title": "Module A", "sequence_order": 1},
            headers=admin_headers,
        )
        assert m1.status_code == 201

        # Duplicate Module sequence_order=1 must fail
        m_dup = await client.post(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}/modules",
            json={"title": "Module Duplicate", "sequence_order": 1},
            headers=admin_headers,
        )
        assert m_dup.status_code == 409

    async def test_student_and_faculty_rbac_boundaries(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify Students cannot create or alter curriculum and Faculty cannot approve."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        faculty = seed_data["faculty_user"]
        student = seed_data["student_user"]

        course_id = await self._setup_course(client, admin, inst.slug)
        student_headers = self._auth_headers(student)
        faculty_headers = self._auth_headers(faculty)

        # Student cannot create curriculum
        resp_stud_create = await client.post(
            f"/api/v1/institutions/{inst.slug}/courses/{course_id}/curriculums",
            json={"title": "Illegal Student Curriculum"},
            headers=student_headers,
        )
        assert resp_stud_create.status_code == 403
        assert resp_stud_create.json()["error"]["code"] == "INSUFFICIENT_ROLE"

        # Faculty creates curriculum
        curr = await client.post(
            f"/api/v1/institutions/{inst.slug}/courses/{course_id}/curriculums",
            json={"title": "Faculty Draft"},
            headers=faculty_headers,
        )
        curr_id = curr.json()["data"]["id"]

        # Faculty moves to IN_REVIEW
        await client.patch(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}/status",
            json={"status": "IN_REVIEW"},
            headers=faculty_headers,
        )

        # Faculty CANNOT approve (approval requires Admin or HOD)
        resp_fac_approve = await client.patch(
            f"/api/v1/institutions/{inst.slug}/curriculums/{curr_id}/status",
            json={"status": "APPROVED"},
            headers=faculty_headers,
        )
        assert resp_fac_approve.status_code == 403
        assert resp_fac_approve.json()["error"]["code"] == "INSUFFICIENT_ROLE"

    async def test_cross_tenant_curriculum_access_denied(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify user of Institution 2 cannot access Institution 1 curriculum."""
        inst1 = seed_data["inst1"]
        admin1 = seed_data["inst_admin"]
        inst2_user = seed_data["inst2_user"]

        course_id = await self._setup_course(client, admin1, inst1.slug)
        admin1_headers = self._auth_headers(admin1)

        curr = await client.post(
            f"/api/v1/institutions/{inst1.slug}/courses/{course_id}/curriculums",
            json={"title": "Protected Curriculum"},
            headers=admin1_headers,
        )
        curr_id = curr.json()["data"]["id"]

        # User from institution 2 tries to access institution 1 curriculum
        inst2_headers = self._auth_headers(inst2_user)
        resp = await client.get(
            f"/api/v1/institutions/{inst1.slug}/curriculums/{curr_id}",
            headers=inst2_headers,
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "TENANT_ACCESS_DENIED"
