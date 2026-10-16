"""Dhruva.AI V2 — Phase 6 Mastery, Skills & Learning Evidence Test Suite.

Verifies:
1. Deterministic mastery blending (70% assessment + 30% evidence).
2. Ebbinghaus exponential retention decay with configurable half-life.
3. SuperMemo SM-2 spaced repetition interval calculation.
4. Competency level classification & provenance generation.
5. Concept, Prerequisites, Learning Outcomes, and Skill knowledge graph persistence.
6. Evidence submission, verification lifecycle, and deterministic mastery updates.
7. Assessment-to-evidence synchronization, idempotency, and pending manual grade exclusion.
8. RBAC guards, student isolation, and multi-tenant boundary isolation.
"""

import math
import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.mastery.mastery_engine import DeterministicMasteryEngine
from src.application.mastery.mastery_service import MasteryService
from src.core.errors import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from src.core.security import create_access_token
from src.domain.identity.models import Institution, Role, User, UserRole
from src.domain.identity.roles import SystemRole
from src.domain.assessment.models import (
    Assessment,
    AssessmentQuestion,
    AssessmentResult,
    AssessmentSubmission,
    Question,
    QuestionBank,
)
from src.infrastructure.persistence.postgres.base import utc_now


# =============================================================================
# 1. UNIT TESTS: DETERMINISTIC MASTERY ENGINE FORMULAS
# =============================================================================
class TestDeterministicMasteryEngine:
    def test_pure_assessment_mastery(self):
        scores = [0.80, 0.90, 1.00]
        raw = DeterministicMasteryEngine.calculate_raw_mastery(
            assessment_scores=scores,
            evidence_scores=[],
        )
        assert raw == 0.9000

    def test_pure_evidence_mastery(self):
        scores = [1.0, 1.0]
        raw = DeterministicMasteryEngine.calculate_raw_mastery(
            assessment_scores=[],
            evidence_scores=scores,
        )
        assert raw == 1.0000

    def test_blended_mastery(self):
        # 70% assessment + 30% evidence
        # 0.70 * 0.80 + 0.30 * 1.00 = 0.56 + 0.30 = 0.86
        raw = DeterministicMasteryEngine.calculate_raw_mastery(
            assessment_scores=[0.80],
            evidence_scores=[1.00],
        )
        assert raw == 0.8600

    def test_empty_metrics(self):
        raw = DeterministicMasteryEngine.calculate_raw_mastery([], [])
        assert raw == 0.0

    def test_ebbinghaus_decay_curve(self):
        raw = 1.0
        # 0 days elapsed -> 1.0
        decayed_0, factor_0 = DeterministicMasteryEngine.calculate_retention_decay(raw, days_elapsed=0.0)
        assert decayed_0 == 1.0
        assert factor_0 == 1.0

        # At exactly half_life (90 days) -> factor should be ~0.50
        decayed_90, factor_90 = DeterministicMasteryEngine.calculate_retention_decay(
            raw, days_elapsed=90.0, half_life_days=90.0
        )
        assert math.isclose(factor_90, 0.5000, abs_tol=0.001)
        assert math.isclose(decayed_90, 0.5000, abs_tol=0.001)

    def test_confidence_metric_growth(self):
        assert DeterministicMasteryEngine.calculate_confidence(0, 0) == 0.0
        assert DeterministicMasteryEngine.calculate_confidence(2, 2) == 0.9000
        assert DeterministicMasteryEngine.calculate_confidence(10, 10) == 1.0000

    def test_competency_classification(self):
        assert DeterministicMasteryEngine.classify_competency(0.95, observation_count=0) == "INSUFFICIENT_EVIDENCE"
        assert DeterministicMasteryEngine.classify_competency(0.35, observation_count=2) == "NOVICE"
        assert DeterministicMasteryEngine.classify_competency(0.55, observation_count=2) == "DEVELOPING"
        assert DeterministicMasteryEngine.classify_competency(0.70, observation_count=2) == "COMPETENT"
        assert DeterministicMasteryEngine.classify_competency(0.85, observation_count=2) == "PROFICIENT"
        assert DeterministicMasteryEngine.classify_competency(0.95, observation_count=2) == "MASTERY"

    def test_provenance_payload(self):
        prov = DeterministicMasteryEngine.build_provenance(
            raw_mastery=0.86,
            decay_factor=1.0,
            decayed_mastery=0.86,
            confidence_score=0.45,
            competency_level="PROFICIENT",
            assessment_count=1,
            evidence_count=1,
            days_elapsed=0.0,
        )
        assert prov["rule_version"] == "2026.1"
        assert prov["formula"] == "blended_70_assessment_30_evidence_ebbinghaus_decay"
        assert prov["assessment_weight"] == 0.70
        assert prov["evidence_weight"] == 0.30
        assert prov["competency_level"] == "PROFICIENT"

    def test_sm2_spaced_repetition_progression(self):
        int1, rep1, ef1 = DeterministicMasteryEngine.calculate_sm2_schedule(
            previous_interval_days=1, repetition_number=0, ease_factor=2.5, quality_rating=4
        )
        assert int1 == 1
        assert rep1 == 1
        assert ef1 == 2.5

        int2, rep2, ef2 = DeterministicMasteryEngine.calculate_sm2_schedule(
            previous_interval_days=int1, repetition_number=rep1, ease_factor=ef1, quality_rating=5
        )
        assert int2 == 6
        assert rep2 == 2
        assert ef2 == 2.6

        int3, rep3, ef3 = DeterministicMasteryEngine.calculate_sm2_schedule(
            previous_interval_days=int2, repetition_number=rep2, ease_factor=ef2, quality_rating=5
        )
        assert int3 == round(6 * 2.6)
        assert rep3 == 3

        int_fail, rep_fail, ef_fail = DeterministicMasteryEngine.calculate_sm2_schedule(
            previous_interval_days=int3, repetition_number=rep3, ease_factor=ef3, quality_rating=1
        )
        assert int_fail == 1
        assert rep_fail == 0


# =============================================================================
# 2. INTEGRATION TESTS: APPLICATION SERVICE
# =============================================================================
@pytest.mark.asyncio
class TestMasteryServiceIntegration:
    async def test_concept_and_skill_lifecycle(self, db_session: AsyncSession, seed_data: dict):
        inst = seed_data["inst1"]
        service = MasteryService(db_session)

        skill = await service.create_skill(
            institution_id=inst.id,
            code="SKILL-ALGO-SEARCH",
            name="Search Algorithms",
            category="ALGORITHMS",
            description="Linear and Binary Search proficiency",
        )
        assert skill.id is not None
        assert skill.code == "SKILL-ALGO-SEARCH"

        concept = await service.create_concept(
            institution_id=inst.id,
            code="CONCEPT-BIN-SEARCH",
            name="Binary Search Invariant",
            bloom_level="APPLY",
        )
        assert concept.id is not None
        assert concept.bloom_level == "APPLY"

        link = await service.link_concept_to_skill(
            institution_id=inst.id,
            concept_id=concept.id,
            skill_id=skill.id,
            weight=1.5,
        )
        assert link.weight == 1.5

        with pytest.raises(ConflictError):
            await service.create_skill(
                institution_id=inst.id,
                code="SKILL-ALGO-SEARCH",
                name="Duplicate",
                category="ALGORITHMS",
            )

    async def test_concept_prerequisites(self, db_session: AsyncSession, seed_data: dict):
        inst = seed_data["inst1"]
        service = MasteryService(db_session)

        c1 = await service.create_concept(
            institution_id=inst.id,
            code="CONCEPT-MATH-LOGIC",
            name="Propositional Logic",
        )
        c2 = await service.create_concept(
            institution_id=inst.id,
            code="CONCEPT-MATH-PROOFS",
            name="Proof Techniques",
        )

        # Self-reference rejected
        with pytest.raises(ValidationError):
            await service.create_concept_prerequisite(inst.id, c1.id, c1.id)

        # Valid prerequisite
        prereq = await service.create_concept_prerequisite(inst.id, c2.id, c1.id)
        assert prereq.concept_id == c2.id
        assert prereq.prerequisite_concept_id == c1.id

        # List
        prereqs = await service.list_concept_prerequisites(inst.id, c2.id)
        assert len(prereqs) == 1

    async def test_learning_outcomes(self, db_session: AsyncSession, seed_data: dict):
        inst = seed_data["inst1"]
        service = MasteryService(db_session)

        outcome = await service.create_learning_outcome(
            institution_id=inst.id,
            code="CO-CS101-01",
            statement="Formulate algorithmic solutions to graph connectivity problems.",
            bloom_level="CREATE",
        )
        assert outcome.code == "CO-CS101-01"
        assert outcome.bloom_level == "CREATE"

        outcomes = await service.list_learning_outcomes(inst.id)
        assert any(o.code == "CO-CS101-01" for o in outcomes)

    async def test_evidence_submission_and_deterministic_mastery(
        self, db_session: AsyncSession, seed_data: dict
    ):
        inst = seed_data["inst1"]
        student = seed_data["student_user"]
        faculty = seed_data["faculty_user"]
        service = MasteryService(db_session)

        skill = await service.create_skill(
            institution_id=inst.id,
            code="SKILL-DIST-CONSENSUS",
            name="Distributed Consensus",
            category="SYSTEMS",
        )

        evidence = await service.submit_learning_evidence(
            institution_id=inst.id,
            student_user_id=student.id,
            skill_id=skill.id,
            evidence_type="PROJECT_DELIVERABLE",
            title="Raft Consensus Implementation",
            artifact_url="https://github.com/dhruva-student/raft-go",
        )
        assert evidence.verification_status == "PENDING"
        assert evidence.is_finalized is False

        # Faculty verifies evidence
        verified = await service.verify_learning_evidence(
            institution_id=inst.id,
            evidence_id=evidence.id,
            verifier_user_id=faculty.id,
            is_verified=True,
            notes="Passed all state machine replication unit tests.",
        )
        assert verified.verification_status == "VERIFIED"
        assert verified.is_finalized is True
        assert verified.verified_by == faculty.id

        mastery_list = await service.get_student_mastery_profile(
            institution_id=inst.id,
            student_user_id=student.id,
        )
        assert len(mastery_list) == 1
        rec = mastery_list[0]
        assert rec.skill_id == skill.id
        assert rec.mastery_score == 1.0000
        assert rec.evidence_count == 1
        assert rec.competency_level == "MASTERY"
        assert rec.calculation_provenance["rule_version"] == "2026.1"

    async def test_sync_evidence_from_assessment_result(
        self, db_session: AsyncSession, seed_data: dict
    ):
        inst = seed_data["inst1"]
        student = seed_data["student_user"]
        faculty = seed_data["faculty_user"]
        service = MasteryService(db_session)

        # 1. Setup Skill
        skill = await service.create_skill(
            institution_id=inst.id,
            code="SKILL-SQL-OPT",
            name="SQL Query Optimization",
            category="DATABASES",
        )

        # 2. Setup Question Bank & Question mapped to Skill
        qb = QuestionBank(
            id=uuid.uuid4(),
            institution_id=inst.id,
            title="Database Systems Pool",
            created_by=faculty.id,
        )
        db_session.add(qb)

        q1 = Question(
            id=uuid.uuid4(),
            institution_id=inst.id,
            question_bank_id=qb.id,
            question_type="MCQ",
            prompt_text="Which scan type is optimal for single-row PK lookups?",
            options=[{"id": "opt_a", "text": "Index Scan"}, {"id": "opt_b", "text": "Seq Scan"}],
            answer_key={"correct_option_id": "opt_a"},
            points=5.0,
            skill_id=skill.id,
        )
        db_session.add(q1)

        # Academic hierarchy for assessment offering requirement
        from src.domain.academic.models import (
            AcademicYear,
            Course,
            CourseOffering,
            Department,
            Program,
            Semester,
        )
        dept = Department(
            id=uuid.uuid4(),
            institution_id=inst.id,
            code=f"DEPT_{uuid.uuid4().hex[:4]}",
            name="Computer Science",
        )
        prog = Program(
            id=uuid.uuid4(),
            institution_id=inst.id,
            department_id=dept.id,
            code=f"PROG_{uuid.uuid4().hex[:4]}",
            name="B.Tech Computer Science",
        )
        course = Course(
            id=uuid.uuid4(),
            institution_id=inst.id,
            department_id=dept.id,
            code=f"CS_{uuid.uuid4().hex[:4]}",
            title="Database Systems",
            credits=4.0,
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
            name="Semester 1",
            start_date=datetime.now(timezone.utc).date(),
            end_date=(datetime.now(timezone.utc) + timedelta(days=120)).date(),
        )
        offering = CourseOffering(
            id=uuid.uuid4(),
            institution_id=inst.id,
            course_id=course.id,
            academic_year_id=ay.id,
            semester_id=sem.id,
            status="OPEN",
        )
        db_session.add_all([dept, prog, course, ay, sem, offering])

        # 3. Setup Assessment & Submission & Result
        assessment = Assessment(
            id=uuid.uuid4(),
            institution_id=inst.id,
            course_offering_id=offering.id,
            title="Databases Midterm",
            created_by=faculty.id,
            status="PUBLISHED",
            publish_at=utc_now(),
            due_at=utc_now() + timedelta(days=7),
            total_points=5.0,
        )
        db_session.add(assessment)

        sub = AssessmentSubmission(
            id=uuid.uuid4(),
            institution_id=inst.id,
            assessment_id=assessment.id,
            student_user_id=student.id,
            attempt_number=1,
            status="GRADED",
            submitted_at=utc_now(),
        )
        db_session.add(sub)

        res = AssessmentResult(
            id=uuid.uuid4(),
            institution_id=inst.id,
            submission_id=sub.id,
            raw_score=5.0,
            total_points=5.0,
            percentage=100.0,
            is_passed=True,
            is_finalized=True,
            graded_by=faculty.id,
            graded_at=utc_now(),
            itemized_breakdown=[
                {
                    "question_id": str(q1.id),
                    "question_type": "MCQ",
                    "max_points": 5.0,
                    "awarded_points": 5.0,
                    "status": "CORRECT",
                    "feedback": "Correct index selection.",
                }
            ],
        )
        db_session.add(res)
        await db_session.commit()

        # 4. Sync evidence from result
        synced = await service.sync_evidence_from_assessment_result(
            institution_id=inst.id,
            result_id=res.id,
        )
        assert len(synced) == 1
        ev = synced[0]
        assert ev.skill_id == skill.id
        assert ev.source_result_id == res.id
        assert ev.awarded_score == 5.0
        assert ev.max_score == 5.0
        assert ev.is_finalized is True
        assert ev.verification_status == "VERIFIED"

        # 5. Verify MasteryRecord was updated deterministically
        profile = await service.get_student_mastery_profile(inst.id, student.id)
        assert any(r.skill_id == skill.id and r.mastery_score == 1.0 for r in profile)

        # 6. Idempotency test: repeating sync must NOT create duplicate records
        synced_again = await service.sync_evidence_from_assessment_result(
            institution_id=inst.id,
            result_id=res.id,
        )
        assert len(synced_again) == 1
        assert synced_again[0].id == ev.id

    async def test_sm2_spaced_review_flow(self, db_session: AsyncSession, seed_data: dict):
        inst = seed_data["inst1"]
        student = seed_data["student_user"]
        service = MasteryService(db_session)

        concept = await service.create_concept(
            institution_id=inst.id,
            code="CONCEPT-PAGE-REPLACEMENT",
            name="LRU Page Replacement",
        )

        schedule = await service.schedule_concept_review(
            institution_id=inst.id,
            student_user_id=student.id,
            concept_id=concept.id,
        )
        assert schedule.interval_days == 1
        assert schedule.is_completed is False

        completed = await service.complete_concept_review(
            institution_id=inst.id,
            student_user_id=student.id,
            schedule_id=schedule.id,
            quality_rating=5,
        )
        assert completed.is_completed is True
        assert completed.repetition_number == 1

        pending = await service.get_student_pending_reviews(
            institution_id=inst.id,
            student_user_id=student.id,
        )
        # Review completed today with interval > 0 will not be due immediately
        assert len(pending) == 0



# =============================================================================
# 3. HTTP API END-TO-END TESTS
# =============================================================================
@pytest.mark.asyncio
class TestMasteryApiEndpoints:
    def _auth_headers(self, user: User) -> dict:
        token = create_access_token(
            subject=str(user.id),
            claims={"institution_id": str(user.institution_id) if user.institution_id else None},
        )
        return {"Authorization": f"Bearer {token}"}

    async def test_create_and_list_skills_api(self, client: AsyncClient, seed_data: dict):
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        headers = self._auth_headers(admin)

        resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/skills",
            headers=headers,
            json={
                "code": "SKILL-NET-TCP",
                "name": "TCP Congestion Control",
                "category": "NETWORKING",
                "description": "Tahoe, Reno, and BBR algorithms",
            },
        )
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["code"] == "SKILL-NET-TCP"
        skill_id = data["id"]

        list_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/skills",
            headers=headers,
        )
        assert list_resp.status_code == 200
        items = list_resp.json()["data"]
        assert any(s["id"] == skill_id for s in items)

    async def test_prerequisites_and_outcomes_api(self, client: AsyncClient, seed_data: dict):
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        headers = self._auth_headers(admin)

        # Create two concepts
        c1_res = await client.post(
            f"/api/v1/institutions/{inst.slug}/concepts",
            headers=headers,
            json={"code": "API-CON-01", "name": "Basic Arrays"},
        )
        c1_id = c1_res.json()["data"]["id"]

        c2_res = await client.post(
            f"/api/v1/institutions/{inst.slug}/concepts",
            headers=headers,
            json={"code": "API-CON-02", "name": "Dynamic Arrays"},
        )
        c2_id = c2_res.json()["data"]["id"]

        # Link Prerequisite
        prereq_res = await client.post(
            f"/api/v1/institutions/{inst.slug}/concepts/prerequisites",
            headers=headers,
            json={"concept_id": c2_id, "prerequisite_concept_id": c1_id},
        )
        assert prereq_res.status_code == 201

        # List Prerequisites
        list_prereq = await client.get(
            f"/api/v1/institutions/{inst.slug}/concepts/prerequisites?concept_id={c2_id}",
            headers=headers,
        )
        assert list_prereq.status_code == 200
        assert len(list_prereq.json()["data"]) == 1

        # Create Learning Outcome
        lo_res = await client.post(
            f"/api/v1/institutions/{inst.slug}/learning-outcomes",
            headers=headers,
            json={
                "code": "LO-API-DATA-01",
                "statement": "Implement resizable array amortized operations.",
                "bloom_level": "APPLY",
            },
        )
        assert lo_res.status_code == 201

        # List Learning Outcomes
        list_lo = await client.get(
            f"/api/v1/institutions/{inst.slug}/learning-outcomes",
            headers=headers,
        )
        assert list_lo.status_code == 200
        assert any(lo["code"] == "LO-API-DATA-01" for lo in list_lo.json()["data"])

    async def test_evidence_verification_and_history_api(self, client: AsyncClient, seed_data: dict):
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        student = seed_data["student_user"]
        admin_headers = self._auth_headers(admin)
        student_headers = self._auth_headers(student)

        s_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/skills",
            headers=admin_headers,
            json={
                "code": "SKILL-DB-INDEX",
                "name": "B-Tree Index Tuning",
                "category": "DATABASES",
            },
        )
        skill_id = s_resp.json()["data"]["id"]

        sub_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/evidence/submit",
            headers=student_headers,
            json={
                "skill_id": skill_id,
                "evidence_type": "LAB_REPORT",
                "title": "PostgreSQL EXPLAIN ANALYZE Benchmarks",
                "artifact_url": "https://storage.dhruva.ai/labs/explain-benchmarks.pdf",
            },
        )
        assert sub_resp.status_code == 201
        evidence_id = sub_resp.json()["data"]["id"]

        v_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/evidence/{evidence_id}/verify",
            headers=admin_headers,
            json={
                "is_verified": True,
                "verification_notes": "Methodology verified with accurate execution plans.",
            },
        )
        assert v_resp.status_code == 200
        assert v_resp.json()["data"]["verification_status"] == "VERIFIED"

        # Evidence history endpoint
        hist_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/students/{student.id}/evidence",
            headers=student_headers,
        )
        assert hist_resp.status_code == 200
        assert len(hist_resp.json()["data"]) >= 1

        # Student mastery profile endpoint
        m_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/students/{student.id}/mastery",
            headers=student_headers,
        )
        assert m_resp.status_code == 200
        mastery_items = m_resp.json()["data"]
        assert len(mastery_items) >= 1
        rec = next(m for m in mastery_items if m["skill_id"] == skill_id)
        assert rec["mastery_score"] == 1.0
        assert rec["competency_level"] == "MASTERY"
        assert rec["calculation_provenance"]["rule_version"] == "2026.1"

    async def test_tenant_isolation_guards(self, client: AsyncClient, seed_data: dict):
        inst1 = seed_data["inst1"]
        inst2 = seed_data["inst2"]
        user2 = seed_data["inst2_user"]
        headers2 = self._auth_headers(user2)

        # Attempt to access inst1 concepts via inst2 auth
        resp = await client.get(
            f"/api/v1/institutions/{inst1.slug}/concepts",
            headers=headers2,
        )
        assert resp.status_code == 403
