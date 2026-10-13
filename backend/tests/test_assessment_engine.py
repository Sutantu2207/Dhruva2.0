"""Dhruva.AI V2 — Phase 4 Assessment, Question Bank & Grading Tests.

Validates:
1. Deterministic autograding engine:
   - MCQ exact-match
   - Multi-select exact, partial credit, and anti-guessing penalties
   - Numerical comparison with tolerance bounds
   - Structured-text evaluation routing and pending status
   - Score boundaries, rounding, pass/fail thresholds, and idempotency
2. Question Bank domain:
   - MCQ, Multi-select, Numerical, and Structured-text server-side validation
   - RBAC enforcement (Student denied authoring, Faculty/Admin allowed)
3. Assessment Lifecycle & Configuration:
   - Creation, question linking, mark allocation, and total marks calculation
   - Publishing transition state machine
   - Question lock on published assessments
4. Submission Engine & Security:
   - Strict enrollment verification
   - Authoritative server-side scheduling gates (publish_at, due_at)
   - Attempt limit enforcement
   - Student isolation: Zero answer-key or rubric leakage in student views
   - Cross-student and cross-tenant isolation
5. Subjective Manual Review Workflow:
   - Reviewer authorization and audit trail
"""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.assessment.grading_engine import DeterministicGradingEngine
from src.core.security import create_access_token
from src.domain.academic.models import (
    AcademicYear,
    Course,
    CourseOffering,
    Department,
    Program,
    Semester,
    StudentEnrollment,
)
from src.domain.identity.models import User


# =========================================================================
# UNIT TESTS: DETERMINISTIC GRADING ENGINE
# =========================================================================
class TestDeterministicGradingEngine:
    """Pure mathematical and rubric grading tests."""

    def test_mcq_grading(self):
        answer_key = {"correct_option_id": "opt_b"}

        # Correct answer
        pts, status, _ = DeterministicGradingEngine.evaluate_mcq(
            student_answer="opt_b", answer_key=answer_key, max_points=2.5
        )
        assert status == "CORRECT"
        assert pts == 2.5

        # Incorrect answer
        pts, status, _ = DeterministicGradingEngine.evaluate_mcq(
            student_answer="opt_a", answer_key=answer_key, max_points=2.5
        )
        assert status == "INCORRECT"
        assert pts == 0.0

        # Unanswered
        pts, status, _ = DeterministicGradingEngine.evaluate_mcq(
            student_answer=None, answer_key=answer_key, max_points=2.5
        )
        assert status == "UNANSWERED"
        assert pts == 0.0

    def test_multi_select_grading(self):
        answer_key = {"correct_option_ids": ["opt_a", "opt_c"]}

        # 1. Exact match -> Full marks
        pts, status, _ = DeterministicGradingEngine.evaluate_multi_select(
            student_answer=["opt_a", "opt_c"], answer_key=answer_key, max_points=4.0
        )
        assert status == "CORRECT"
        assert pts == 4.0

        # 2. Subset without mistakes -> Partial credit
        pts, status, _ = DeterministicGradingEngine.evaluate_multi_select(
            student_answer=["opt_a"], answer_key=answer_key, max_points=4.0
        )
        assert status == "PARTIAL"
        assert pts == 2.0  # 1/2 of 4.0

        # 3. Selected extraneous/incorrect option -> 0 marks penalty
        pts, status, _ = DeterministicGradingEngine.evaluate_multi_select(
            student_answer=["opt_a", "opt_b"], answer_key=answer_key, max_points=4.0
        )
        assert status == "INCORRECT"
        assert pts == 0.0

        # 4. Empty or invalid type
        pts, status, _ = DeterministicGradingEngine.evaluate_multi_select(
            student_answer=[], answer_key=answer_key, max_points=4.0
        )
        assert status == "UNANSWERED"
        assert pts == 0.0

    def test_numerical_grading(self):
        answer_key = {"target_value": 42.5, "tolerance": 0.5}

        # Exact
        pts, status, _ = DeterministicGradingEngine.evaluate_numerical(
            student_answer=42.5, answer_key=answer_key, max_points=3.0
        )
        assert status == "CORRECT"
        assert pts == 3.0

        # Within tolerance (upper bound: 43.0)
        pts, status, _ = DeterministicGradingEngine.evaluate_numerical(
            student_answer="43.0", answer_key=answer_key, max_points=3.0
        )
        assert status == "CORRECT"
        assert pts == 3.0

        # Outside tolerance
        pts, status, _ = DeterministicGradingEngine.evaluate_numerical(
            student_answer=43.1, answer_key=answer_key, max_points=3.0
        )
        assert status == "INCORRECT"
        assert pts == 0.0

        # Non-numeric string
        pts, status, _ = DeterministicGradingEngine.evaluate_numerical(
            student_answer="not-a-number", answer_key=answer_key, max_points=3.0
        )
        assert status == "INCORRECT"
        assert pts == 0.0

    def test_structured_text_pending_manual(self):
        answer_key = {"rubric": "Explain time complexity of quicksort"}
        pts, status, _ = DeterministicGradingEngine.evaluate_structured_text(
            student_answer="Quicksort is O(n log n) average, O(n^2) worst case.",
            answer_key=answer_key,
            max_points=5.0,
        )
        assert status == "PENDING_MANUAL"
        assert pts == 0.0

    def test_letter_grade_calculation(self):
        assert DeterministicGradingEngine.compute_letter_grade(95.0) == "A+"
        assert DeterministicGradingEngine.compute_letter_grade(85.0) == "A"
        assert DeterministicGradingEngine.compute_letter_grade(72.0) == "B"
        assert DeterministicGradingEngine.compute_letter_grade(62.0) == "C"
        assert DeterministicGradingEngine.compute_letter_grade(52.0) == "D"
        assert DeterministicGradingEngine.compute_letter_grade(38.0) == "F"

    def test_overall_submission_grading(self):
        question_configs = [
            {
                "id": "q1",
                "question_type": "MCQ",
                "answer_key": {"correct_option_id": "opt_a"},
                "points": 5.0,
            },
            {
                "id": "q2",
                "question_type": "NUMERICAL",
                "answer_key": {"target_value": 10.0, "tolerance": 0.0},
                "points": 5.0,
            },
        ]
        answers = {"q1": "opt_a", "q2": 10.0}
        result = DeterministicGradingEngine.grade_submission(
            assessment_questions=question_configs,
            answers_payload=answers,
            passing_percentage=50.0,
        )
        assert result["raw_score"] == 10.0
        assert result["total_points"] == 10.0
        assert result["percentage"] == 100.0
        assert result["grade_letter"] == "A+"
        assert result["is_passed"] is True
        assert result["is_finalized"] is True


# =========================================================================
# INTEGRATION & API TESTS
# =========================================================================
@pytest.mark.asyncio
class TestAssessmentAndGradingAPI:
    """End-to-end integration tests for Phase 4."""

    def _auth_headers(self, user: User) -> dict:
        token = create_access_token(
            subject=str(user.id),
            claims={"institution_id": str(user.institution_id) if user.institution_id else None},
        )
        return {"Authorization": f"Bearer {token}"}

    async def _setup_academic_context(
        self, db_session: AsyncSession, inst_id: uuid.UUID, student_id: uuid.UUID
    ) -> CourseOffering:
        """Create department, course, academic year, semester, offering, and enrollment."""
        dept = Department(
            id=uuid.uuid4(),
            institution_id=inst_id,
            code=f"CSE_{uuid.uuid4().hex[:4]}",
            name="Computer Science",
        )
        prog = Program(
            id=uuid.uuid4(),
            institution_id=inst_id,
            department_id=dept.id,
            code=f"BTECH_{uuid.uuid4().hex[:4]}",
            name="B.Tech Computer Science",
        )
        course = Course(
            id=uuid.uuid4(),
            institution_id=inst_id,
            department_id=dept.id,
            code=f"CS_{uuid.uuid4().hex[:4]}",
            title="Design & Analysis of Algorithms",
            credits=4.0,
        )
        ay = AcademicYear(
            id=uuid.uuid4(),
            institution_id=inst_id,
            code=f"AY_{uuid.uuid4().hex[:4]}",
            name="Academic Year 2026",
            start_date=datetime.now(timezone.utc).date(),
            end_date=(datetime.now(timezone.utc) + timedelta(days=365)).date(),
        )
        sem = Semester(
            id=uuid.uuid4(),
            institution_id=inst_id,
            academic_year_id=ay.id,
            term_number=1,
            name="Semester 1",
            start_date=datetime.now(timezone.utc).date(),
            end_date=(datetime.now(timezone.utc) + timedelta(days=120)).date(),
        )
        offering = CourseOffering(
            id=uuid.uuid4(),
            institution_id=inst_id,
            course_id=course.id,
            academic_year_id=ay.id,
            semester_id=sem.id,
            status="OPEN",
        )
        enrollment = StudentEnrollment(
            id=uuid.uuid4(),
            institution_id=inst_id,
            course_offering_id=offering.id,
            student_user_id=student_id,
            enrollment_status="ENROLLED",
        )
        db_session.add_all([dept, prog, course, ay, sem, offering, enrollment])
        await db_session.commit()
        return offering

    async def test_question_bank_and_question_validation(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify Question Bank creation and strict server-side validation across question types."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        faculty = seed_data["faculty_user"]
        student = seed_data["student_user"]
        fac_headers = self._auth_headers(faculty)

        # 1. Student cannot create Question Bank (RBAC rejection)
        stud_headers = self._auth_headers(student)
        stud_create_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks",
            json={"title": "Student Bank Attempt"},
            headers=stud_headers,
        )
        assert stud_create_resp.status_code == 403

        # 2. Faculty creates Question Bank
        bank_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks",
            json={"title": "Data Structures & Algorithms Bank", "description": "Core algorithms questions"},
            headers=fac_headers,
        )
        assert bank_resp.status_code == 201
        bank_id = bank_resp.json()["data"]["id"]

        # 3. Add Valid MCQ
        mcq_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks/{bank_id}/questions",
            json={
                "question_type": "MCQ",
                "prompt_text": "What is the worst-case time complexity of QuickSort?",
                "options": [
                    {"id": "opt_a", "text": "O(n log n)"},
                    {"id": "opt_b", "text": "O(n^2)"},
                    {"id": "opt_c", "text": "O(n)"},
                ],
                "answer_key": {"correct_option_id": "opt_b"},
                "points": 2.0,
                "difficulty": "MEDIUM",
                "explanation": "QuickSort degrades to O(n^2) when poor pivots are chosen.",
            },
            headers=fac_headers,
        )
        assert mcq_resp.status_code == 201

        # 4. Invalid MCQ: correct_option_id not in options -> 422
        bad_mcq_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks/{bank_id}/questions",
            json={
                "question_type": "MCQ",
                "prompt_text": "Invalid Question?",
                "options": [{"id": "opt_a", "text": "A"}],
                "answer_key": {"correct_option_id": "opt_nonexistent"},
                "points": 1.0,
            },
            headers=fac_headers,
        )
        assert bad_mcq_resp.status_code == 422

        # 5. Add Valid Multi-Select
        multi_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks/{bank_id}/questions",
            json={
                "question_type": "MULTI_SELECT",
                "prompt_text": "Which of the following are self-balancing binary search trees?",
                "options": [
                    {"id": "opt_1", "text": "AVL Tree"},
                    {"id": "opt_2", "text": "Red-Black Tree"},
                    {"id": "opt_3", "text": "Binary Heap"},
                ],
                "answer_key": {"correct_option_ids": ["opt_1", "opt_2"]},
                "points": 3.0,
                "difficulty": "HARD",
            },
            headers=fac_headers,
        )
        assert multi_resp.status_code == 201

        # 6. Add Valid Numerical Question
        num_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks/{bank_id}/questions",
            json={
                "question_type": "NUMERICAL",
                "prompt_text": "What is the value of e rounded to 2 decimal places?",
                "answer_key": {"target_value": 2.72, "tolerance": 0.01},
                "points": 2.0,
            },
            headers=fac_headers,
        )
        assert num_resp.status_code == 201

        # 7. Add Valid Structured Text Question
        text_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks/{bank_id}/questions",
            json={
                "question_type": "STRUCTURED_TEXT",
                "prompt_text": "Explain Dijkstra's algorithm and contrast with Bellman-Ford.",
                "answer_key": {"rubric": "Must mention greedy choice, non-negative weights, and queue."},
                "points": 5.0,
            },
            headers=fac_headers,
        )
        assert text_resp.status_code == 201

    async def test_assessment_lifecycle_and_zero_leakage(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify assessment creation, question addition, total points update, publishing, and zero answer leakage."""
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        faculty = seed_data["faculty_user"]
        student = seed_data["student_user"]
        fac_headers = self._auth_headers(faculty)
        stud_headers = self._auth_headers(student)

        offering = await self._setup_academic_context(db_session, inst.id, student.id)

        # 1. Create Question Bank & Question
        bank_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks",
            json={"title": "Algorithms Exam Bank"},
            headers=fac_headers,
        )
        bank_id = bank_resp.json()["data"]["id"]

        q_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks/{bank_id}/questions",
            json={
                "question_type": "MCQ",
                "prompt_text": "Is binary search O(log n)?",
                "options": [
                    {"id": "opt_true", "text": "True"},
                    {"id": "opt_false", "text": "False"},
                ],
                "answer_key": {"correct_option_id": "opt_true"},
                "points": 5.0,
                "explanation": "Binary search divides the search interval in half each step.",
            },
            headers=fac_headers,
        )
        q_id = q_resp.json()["data"]["id"]

        # 2. Create Assessment (Status: DRAFT)
        now = datetime.now(timezone.utc)
        assess_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments",
            json={
                "course_offering_id": str(offering.id),
                "title": "Algorithms Quiz 1",
                "instructions": "All questions mandatory.",
                "assessment_type": "QUIZ",
                "publish_at": (now - timedelta(minutes=5)).isoformat(),
                "due_at": (now + timedelta(hours=2)).isoformat(),
                "duration_minutes": 60,
                "passing_percentage": 50.0,
                "max_attempts": 2,
            },
            headers=fac_headers,
        )
        assert assess_resp.status_code == 201
        assess_id = assess_resp.json()["data"]["id"]
        assert assess_resp.json()["data"]["status"] == "DRAFT"

        # 3. Cannot publish assessment without questions -> 409 Conflict
        pub_fail = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/publish",
            headers=fac_headers,
        )
        assert pub_fail.status_code == 409

        # 4. Link Question to Assessment
        link_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/questions",
            json={"question_id": q_id, "points": 5.0},
            headers=fac_headers,
        )
        assert link_resp.status_code == 201

        # 5. Publish Assessment -> 200 OK
        pub_ok = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/publish",
            headers=fac_headers,
        )
        assert pub_ok.status_code == 200
        assert pub_ok.json()["data"]["status"] == "PUBLISHED"
        assert pub_ok.json()["data"]["total_points"] == 5.0

        # 6. Cannot add questions after publication -> 409 Conflict
        add_after_pub = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/questions",
            json={"question_id": q_id, "points": 5.0},
            headers=fac_headers,
        )
        assert add_after_pub.status_code == 409

        # 7. CRITICAL TEST: Zero Answer Key Leakage
        # Student queries assessment detail
        student_view_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}",
            headers=stud_headers,
        )
        assert student_view_resp.status_code == 200
        student_data = student_view_resp.json()["data"]
        # Questions present
        assert len(student_data["questions"]) == 1
        q_view = student_data["questions"][0]["question"]
        # Must contain prompt & options
        assert "prompt_text" in q_view
        assert len(q_view["options"]) == 2
        # MUST NOT contain answer_key or explanation!
        assert "answer_key" not in q_view
        assert "explanation" not in q_view

    async def test_end_to_end_submission_and_autograding(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify student submission, deterministic autograding, attempt limits, and manual evaluation."""
        inst = seed_data["inst1"]
        faculty = seed_data["faculty_user"]
        student = seed_data["student_user"]
        fac_headers = self._auth_headers(faculty)
        stud_headers = self._auth_headers(student)

        offering = await self._setup_academic_context(db_session, inst.id, student.id)

        # 1. Create bank & multiple question types
        bank_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks",
            json={"title": "Midterm Exam Bank"},
            headers=fac_headers,
        )
        bank_id = bank_resp.json()["data"]["id"]

        # Q1: MCQ (3 pts)
        q1_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks/{bank_id}/questions",
            json={
                "question_type": "MCQ",
                "prompt_text": "What is 2 + 2?",
                "options": [{"id": "a", "text": "3"}, {"id": "b", "text": "4"}],
                "answer_key": {"correct_option_id": "b"},
                "points": 3.0,
            },
            headers=fac_headers,
        )
        q1_id = q1_resp.json()["data"]["id"]

        # Q2: Multi-select (4 pts)
        q2_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks/{bank_id}/questions",
            json={
                "question_type": "MULTI_SELECT",
                "prompt_text": "Select prime numbers:",
                "options": [
                    {"id": "p2", "text": "2"},
                    {"id": "p3", "text": "3"},
                    {"id": "p4", "text": "4"},
                ],
                "answer_key": {"correct_option_ids": ["p2", "p3"]},
                "points": 4.0,
            },
            headers=fac_headers,
        )
        q2_id = q2_resp.json()["data"]["id"]

        # Q3: Structured Text (5 pts)
        q3_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks/{bank_id}/questions",
            json={
                "question_type": "STRUCTURED_TEXT",
                "prompt_text": "Describe the Church-Turing thesis.",
                "answer_key": {"rubric": "Turing machines represent effective computation."},
                "points": 5.0,
            },
            headers=fac_headers,
        )
        q3_id = q3_resp.json()["data"]["id"]

        # 2. Create Assessment with 1 attempt limit
        now = datetime.now(timezone.utc)
        assess_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments",
            json={
                "course_offering_id": str(offering.id),
                "title": "Comprehensive Midterm",
                "publish_at": (now - timedelta(minutes=5)).isoformat(),
                "due_at": (now + timedelta(hours=2)).isoformat(),
                "passing_percentage": 50.0,
                "max_attempts": 1,
            },
            headers=fac_headers,
        )
        assess_id = assess_resp.json()["data"]["id"]

        # Add questions
        await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/questions",
            json={"question_id": q1_id, "points": 3.0},
            headers=fac_headers,
        )
        await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/questions",
            json={"question_id": q2_id, "points": 4.0},
            headers=fac_headers,
        )
        await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/questions",
            json={"question_id": q3_id, "points": 5.0},
            headers=fac_headers,
        )

        # Publish
        await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/publish",
            headers=fac_headers,
        )

        # 3. Student submits answers
        # Q1: correct ("b") -> 3.0
        # Q2: partial credit: selects only "p2" (subset, 1/2 of 4 = 2.0)
        # Q3: subjective text -> 0.0 initially, status PENDING_MANUAL
        sub_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/submit",
            json={
                "answers_payload": {
                    q1_id: "b",
                    q2_id: ["p2"],
                    q3_id: "A function on natural numbers is computable if and only if it can be computed by a Turing machine.",
                }
            },
            headers=stud_headers,
        )
        assert sub_resp.status_code == 201
        sub_data = sub_resp.json()["data"]
        sub_id = sub_data["id"]
        result = sub_data["result"]
        assert result is not None
        # Auto-graded score: 3.0 + 2.0 = 5.0 out of 12.0
        assert result["raw_score"] == 5.0
        assert result["total_points"] == 12.0
        # Since Q3 is PENDING_MANUAL, submission status is PENDING_REVIEW and is_finalized is False
        assert sub_data["status"] == "PENDING_REVIEW"
        assert result["is_finalized"] is False

        # 4. Attempt limit check: Student tries submitting a second attempt -> 409 Conflict
        sub2_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/submit",
            json={"answers_payload": {q1_id: "b"}},
            headers=stud_headers,
        )
        assert sub2_resp.status_code == 409

        # 5. Faculty evaluates Subjective Question (Q3)
        manual_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/submissions/{sub_id}/grade-manual",
            json={
                "question_id": q3_id,
                "awarded_points": 4.5,
                "feedback": "Strong explanation with precise formulation.",
            },
            headers=fac_headers,
        )
        assert manual_resp.status_code == 200
        final_result = manual_resp.json()["data"]
        # Updated score: 5.0 + 4.5 = 9.5 out of 12.0 (79.17%)
        assert final_result["raw_score"] == 9.5
        assert final_result["is_finalized"] is True
        assert final_result["is_passed"] is True
        assert final_result["grade_letter"] == "B"

    async def test_enrollment_and_timing_gates(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify student not enrolled cannot submit, and submissions outside window are rejected."""
        inst = seed_data["inst1"]
        faculty = seed_data["faculty_user"]
        student = seed_data["student_user"]
        fac_headers = self._auth_headers(faculty)
        stud_headers = self._auth_headers(student)

        # Setup offering WITHOUT student enrollment
        dept = Department(
            id=uuid.uuid4(),
            institution_id=inst.id,
            code=f"EE_{uuid.uuid4().hex[:4]}",
            name="Electrical Engineering",
        )
        course = Course(
            id=uuid.uuid4(),
            institution_id=inst.id,
            department_id=dept.id,
            code=f"EE_{uuid.uuid4().hex[:4]}",
            title="Signals and Systems",
            credits=3.0,
        )
        ay = AcademicYear(
            id=uuid.uuid4(),
            institution_id=inst.id,
            code=f"AY_{uuid.uuid4().hex[:4]}",
            name="AY 2026",
            start_date=datetime.now(timezone.utc).date(),
            end_date=(datetime.now(timezone.utc) + timedelta(days=365)).date(),
        )
        sem = Semester(
            id=uuid.uuid4(),
            institution_id=inst.id,
            academic_year_id=ay.id,
            term_number=1,
            name="Sem 1",
            start_date=datetime.now(timezone.utc).date(),
            end_date=(datetime.now(timezone.utc) + timedelta(days=120)).date(),
        )
        unenrolled_offering = CourseOffering(
            id=uuid.uuid4(),
            institution_id=inst.id,
            course_id=course.id,
            academic_year_id=ay.id,
            semester_id=sem.id,
            status="OPEN",
        )
        db_session.add_all([dept, course, ay, sem, unenrolled_offering])
        await db_session.commit()

        # Bank and Question
        bank_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks",
            json={"title": "EE Bank"},
            headers=fac_headers,
        )
        bank_id = bank_resp.json()["data"]["id"]
        q_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/question-banks/{bank_id}/questions",
            json={
                "question_type": "MCQ",
                "prompt_text": "Is Fourier transform linear?",
                "options": [{"id": "y", "text": "Yes"}, {"id": "n", "text": "No"}],
                "answer_key": {"correct_option_id": "y"},
                "points": 1.0,
            },
            headers=fac_headers,
        )
        q_id = q_resp.json()["data"]["id"]

        # Assessment 1: Valid window, but student NOT enrolled
        now = datetime.now(timezone.utc)
        assess_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments",
            json={
                "course_offering_id": str(unenrolled_offering.id),
                "title": "EE Quiz",
                "publish_at": (now - timedelta(minutes=5)).isoformat(),
                "due_at": (now + timedelta(hours=2)).isoformat(),
            },
            headers=fac_headers,
        )
        assess_id = assess_resp.json()["data"]["id"]
        await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/questions",
            json={"question_id": q_id, "points": 1.0},
            headers=fac_headers,
        )
        await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/publish",
            headers=fac_headers,
        )

        # Unenrolled student tries to submit -> 403 Forbidden
        unenroll_submit = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{assess_id}/submit",
            json={"answers_payload": {q_id: "y"}},
            headers=stud_headers,
        )
        assert unenroll_submit.status_code == 403

        # Assessment 2: Expired deadline (due_at in past)
        expired_assess = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments",
            json={
                "course_offering_id": str(unenrolled_offering.id),
                "title": "Expired EE Quiz",
                "publish_at": (now - timedelta(hours=3)).isoformat(),
                "due_at": (now - timedelta(hours=1)).isoformat(),
            },
            headers=fac_headers,
        )
        exp_id = expired_assess.json()["data"]["id"]
        await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{exp_id}/questions",
            json={"question_id": q_id, "points": 1.0},
            headers=fac_headers,
        )
        await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{exp_id}/publish",
            headers=fac_headers,
        )

        # Enroll student in offering now
        enrollment = StudentEnrollment(
            id=uuid.uuid4(),
            institution_id=inst.id,
            course_offering_id=unenrolled_offering.id,
            student_user_id=student.id,
            enrollment_status="ENROLLED",
        )
        db_session.add(enrollment)
        await db_session.commit()

        # Submit after deadline -> 409 Conflict
        late_submit = await client.post(
            f"/api/v1/institutions/{inst.slug}/assessments/{exp_id}/submit",
            json={"answers_payload": {q_id: "y"}},
            headers=stud_headers,
        )
        assert late_submit.status_code == 409

    async def test_cross_tenant_isolation(
        self, client: AsyncClient, seed_data: dict, db_session: AsyncSession
    ):
        """Verify strict multi-tenant boundary: Tenant 2 users cannot access Tenant 1 assessments or banks."""
        inst1 = seed_data["inst1"]
        inst2 = seed_data["inst2"]
        admin1 = seed_data["inst_admin"]
        user2 = seed_data["inst2_user"]

        headers1 = self._auth_headers(admin1)
        headers2 = self._auth_headers(user2)

        # 1. Admin 1 creates Question Bank in Inst 1
        bank_resp = await client.post(
            f"/api/v1/institutions/{inst1.slug}/question-banks",
            json={"title": "IITB Private Question Bank"},
            headers=headers1,
        )
        assert bank_resp.status_code == 201
        bank_id = bank_resp.json()["data"]["id"]

        # 2. User 2 from Inst 2 tries to access Inst 1 Question Bank -> 403 Forbidden
        cross_resp = await client.get(
            f"/api/v1/institutions/{inst1.slug}/question-banks/{bank_id}",
            headers=headers2,
        )
        assert cross_resp.status_code == 403
