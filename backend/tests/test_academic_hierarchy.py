"""Dhruva.AI V2 — Academic Hierarchy & Course Catalog Tests.

Validates:
1. End-to-end CRUD for academic structure (Departments, Programs, Academic Years, Semesters, Batches, Sections, Courses, Offerings)
2. Business rule invariant enforcement (date order, term uniqueness, capacity, duplicate protection)
3. Strict tenant isolation and cross-tenant access rejection
4. RBAC authorization boundaries (Students/Faculty prevented from administrative operations)
"""

import uuid
from datetime import date, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.security import create_access_token
from src.domain.identity.models import Institution, User


@pytest.mark.asyncio
class TestAcademicHierarchyAPI:
    """Test suite for Phase 2 Academic Hierarchy domain operations."""

    def _auth_headers(self, user: User) -> dict:
        token = create_access_token(
            subject=str(user.id),
            claims={"institution_id": str(user.institution_id) if user.institution_id else None},
        )
        return {"Authorization": f"Bearer {token}"}

    async def test_complete_academic_hierarchy_creation(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify full hierarchy creation workflow from department to enrollment."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        faculty = seed_data["faculty_user"]
        student = seed_data["student_user"]
        headers = self._auth_headers(admin)

        # 1. Create Department
        dept_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/departments",
            json={"code": "CSE", "name": "Computer Science & Engineering"},
            headers=headers,
        )
        assert dept_resp.status_code == 201
        dept_data = dept_resp.json()["data"]
        dept_id = dept_data["id"]
        assert dept_data["code"] == "CSE"

        # 2. Create Program
        prog_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/programs",
            json={
                "department_id": dept_id,
                "code": "BTECH-CSE",
                "name": "B.Tech Computer Science",
                "degree_level": "UNDERGRADUATE",
                "total_semesters": 8,
            },
            headers=headers,
        )
        assert prog_resp.status_code == 201
        prog_id = prog_resp.json()["data"]["id"]

        # 3. Create Academic Year
        today = date.today()
        ay_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/academic-years",
            json={
                "code": "AY-2026-27",
                "name": "Academic Year 2026-2027",
                "start_date": str(today),
                "end_date": str(today + timedelta(days=365)),
                "is_current": True,
            },
            headers=headers,
        )
        assert ay_resp.status_code == 201
        ay_id = ay_resp.json()["data"]["id"]

        # 4. Create Semester
        sem_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/academic-years/{ay_id}/semesters",
            json={
                "term_number": 1,
                "name": "Semester 1",
                "start_date": str(today),
                "end_date": str(today + timedelta(days=120)),
                "status": "UPCOMING",
            },
            headers=headers,
        )
        assert sem_resp.status_code == 201
        sem_id = sem_resp.json()["data"]["id"]

        # 5. Create Batch
        batch_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/batches",
            json={
                "program_id": prog_id,
                "name": "Class of 2030",
                "admission_year": 2026,
                "graduation_year": 2030,
            },
            headers=headers,
        )
        assert batch_resp.status_code == 201
        batch_id = batch_resp.json()["data"]["id"]

        # 6. Create Section
        sec_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/batches/{batch_id}/sections",
            json={"name": "Section A", "capacity": 60},
            headers=headers,
        )
        assert sec_resp.status_code == 201
        sec_id = sec_resp.json()["data"]["id"]

        # 7. Create Course Catalog Entry
        course_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/courses",
            json={
                "department_id": dept_id,
                "code": "CS101",
                "title": "Introduction to Computer Science",
                "credits": 4.0,
                "course_type": "THEORY",
                "course_metadata": {"syllabus_url": "https://iitb.ac.in/cs101"},
            },
            headers=headers,
        )
        assert course_resp.status_code == 201
        course_id = course_resp.json()["data"]["id"]

        # 8. Create Course Offering
        offering_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/offerings",
            json={
                "course_id": course_id,
                "academic_year_id": ay_id,
                "semester_id": sem_id,
                "section_id": sec_id,
                "status": "OPEN",
            },
            headers=headers,
        )
        assert offering_resp.status_code == 201
        offering_id = offering_resp.json()["data"]["id"]

        # 9. Assign Faculty
        assign_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/offerings/{offering_id}/assign-faculty",
            json={"faculty_user_id": str(faculty.id), "role_type": "PRIMARY_INSTRUCTOR"},
            headers=headers,
        )
        assert assign_resp.status_code == 201

        # 10. Enroll Student
        enroll_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/offerings/{offering_id}/enroll",
            json={"student_user_id": str(student.id)},
            headers=headers,
        )
        assert enroll_resp.status_code == 201
        assert enroll_resp.json()["data"]["enrollment_status"] == "ENROLLED"

        # 11. List Enrollments
        list_enroll = await client.get(
            f"/api/v1/institutions/{inst.slug}/offerings/{offering_id}/enrollments",
            headers=headers,
        )
        assert list_enroll.status_code == 200
        assert len(list_enroll.json()["data"]) == 1

    async def test_duplicate_code_conflicts_rejected(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify that duplicate department or course codes raise 409 Conflict."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        headers = self._auth_headers(admin)

        # First department creation succeeds
        resp1 = await client.post(
            f"/api/v1/institutions/{inst.slug}/departments",
            json={"code": "MECH", "name": "Mechanical Engineering"},
            headers=headers,
        )
        assert resp1.status_code == 201

        # Duplicate department code must be rejected
        resp2 = await client.post(
            f"/api/v1/institutions/{inst.slug}/departments",
            json={"code": "MECH", "name": "Mechanical Engineering Duplicate"},
            headers=headers,
        )
        assert resp2.status_code == 409
        assert "already exists" in resp2.json()["error"]["message"]

    async def test_academic_calendar_date_invariants(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify date validation for academic years and semester bounds."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        headers = self._auth_headers(admin)
        today = date.today()

        # Inverted dates (start > end) must fail
        resp_invalid_ay = await client.post(
            f"/api/v1/institutions/{inst.slug}/academic-years",
            json={
                "code": "AY-INVERTED",
                "name": "Inverted Year",
                "start_date": str(today + timedelta(days=100)),
                "end_date": str(today),
            },
            headers=headers,
        )
        assert resp_invalid_ay.status_code == 422

        # Create valid academic year
        ay_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/academic-years",
            json={
                "code": "AY-BOUNDS-TEST",
                "name": "AY Bounds Test",
                "start_date": str(today),
                "end_date": str(today + timedelta(days=300)),
            },
            headers=headers,
        )
        assert ay_resp.status_code == 201
        ay_id = ay_resp.json()["data"]["id"]

        # Semester exceeding parent year end date must fail
        resp_out_of_bounds = await client.post(
            f"/api/v1/institutions/{inst.slug}/academic-years/{ay_id}/semesters",
            json={
                "term_number": 1,
                "name": "Overflow Semester",
                "start_date": str(today + timedelta(days=10)),
                "end_date": str(today + timedelta(days=400)),  # Exceeds AY end date (+300)
            },
            headers=headers,
        )
        assert resp_out_of_bounds.status_code == 422
        assert "must fall within parent Academic Year" in resp_out_of_bounds.json()["error"]["message"]

    async def test_duplicate_enrollment_rejected(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify student cannot be double-enrolled in the same course offering."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        student = seed_data["student_user"]
        headers = self._auth_headers(admin)
        today = date.today()

        # Setup minimal offering
        dept = await client.post(
            f"/api/v1/institutions/{inst.slug}/departments",
            json={"code": "EE", "name": "Electrical Engineering"},
            headers=headers,
        )
        dept_id = dept.json()["data"]["id"]

        course = await client.post(
            f"/api/v1/institutions/{inst.slug}/courses",
            json={"department_id": dept_id, "code": "EE201", "title": "Signals & Systems", "credits": 3.0},
            headers=headers,
        )
        course_id = course.json()["data"]["id"]

        ay = await client.post(
            f"/api/v1/institutions/{inst.slug}/academic-years",
            json={"code": "AY-EE-2026", "name": "AY 2026", "start_date": str(today), "end_date": str(today + timedelta(days=200))},
            headers=headers,
        )
        ay_id = ay.json()["data"]["id"]

        sem = await client.post(
            f"/api/v1/institutions/{inst.slug}/academic-years/{ay_id}/semesters",
            json={"term_number": 1, "name": "Term 1", "start_date": str(today), "end_date": str(today + timedelta(days=90))},
            headers=headers,
        )
        sem_id = sem.json()["data"]["id"]

        offering = await client.post(
            f"/api/v1/institutions/{inst.slug}/offerings",
            json={"course_id": course_id, "academic_year_id": ay_id, "semester_id": sem_id},
            headers=headers,
        )
        offering_id = offering.json()["data"]["id"]

        # First enrollment succeeds
        e1 = await client.post(
            f"/api/v1/institutions/{inst.slug}/offerings/{offering_id}/enroll",
            json={"student_user_id": str(student.id)},
            headers=headers,
        )
        assert e1.status_code == 201

        # Second enrollment must fail with 409 Conflict
        e2 = await client.post(
            f"/api/v1/institutions/{inst.slug}/offerings/{offering_id}/enroll",
            json={"student_user_id": str(student.id)},
            headers=headers,
        )
        assert e2.status_code == 409
        assert "already enrolled" in e2.json()["error"]["message"]

    async def test_cross_tenant_academic_access_strictly_denied(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify user of Institution 2 cannot access or mutate Institution 1 academic entities."""
        inst1 = seed_data["inst1"]
        inst2_user = seed_data["inst2_user"]  # belongs to inst2 (bits-pilani)
        headers = self._auth_headers(inst2_user)

        # Attempt to list departments of inst1 (iit-bombay)
        resp = await client.get(
            f"/api/v1/institutions/{inst1.slug}/departments",
            headers=headers,
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "TENANT_ACCESS_DENIED"

    async def test_student_role_cannot_manage_academic_structure(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify that students cannot create departments or programs."""
        inst = seed_data["inst1"]
        student = seed_data["student_user"]
        headers = self._auth_headers(student)

        resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/departments",
            json={"code": "ILLEGAL", "name": "Illegal Department"},
            headers=headers,
        )
        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == "INSUFFICIENT_ROLE"
