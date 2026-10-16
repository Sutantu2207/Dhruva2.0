"""Dhruva.AI V2 — Phase 7 Placement, Projects & Portfolios Test Suite.

Verifies:
1. Deterministic Career Readiness calculation, gap analysis, and explainable provenance.
2. Missing evidence distinction from zero proficiency.
3. Student Project Studio creation, skill/evidence linkage, and submission lifecycle.
4. Faculty verification gate (approval, rejection, revocation with audit reason).
5. Portfolio Builder curation, publication gating, and privacy enforcement (PRIVATE | INSTITUTION | PUBLIC).
6. Placement Officer talent discovery pool, skill filtering, and institutional analytics.
7. Strict RBAC permission guards and cross-tenant boundary isolation.
"""

import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.placement.placement_service import PlacementService
from src.application.placement.readiness_engine import DeterministicReadinessEngine
from src.core.errors import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from src.core.security import create_access_token
from src.domain.identity.models import Institution, Role, User, UserRole
from src.domain.identity.roles import SystemRole
from src.domain.mastery.models import LearningEvidence, MasteryRecord, Skill
from src.domain.placement.models import CareerGoal, CareerReadiness, Portfolio, Project
from src.infrastructure.persistence.postgres.base import utc_now


# =============================================================================
# 1. UNIT TESTS: DETERMINISTIC READINESS ENGINE
# =============================================================================
class TestDeterministicReadinessEngine:
    class MockSkill:
        def __init__(self, s_id: uuid.UUID, code: str, name: str, category: str = "DATABASES"):
            self.id = s_id
            self.code = code
            self.name = name
            self.category = category

    class MockMastery:
        def __init__(self, s_id: uuid.UUID, score: float, decay: float = 1.0, confidence: float = 1.0):
            self.skill_id = s_id
            self.mastery_score = score
            self.decay_factor = decay
            self.confidence_score = confidence

    def test_zero_required_skills(self):
        res = DeterministicReadinessEngine.evaluate_career_readiness(
            target_role="Backend Engineer",
            required_skill_ids=[],
            skills_by_id={},
            mastery_by_skill_id={},
            verified_project_skill_ids=[],
        )
        assert res["readiness_score"] == 0.0
        assert res["matching_skills_count"] == 0
        assert res["total_required_skills"] == 0
        assert res["calculation_provenance"]["rule_version"] == "2026.1"

    def test_full_readiness_all_skills_met(self):
        s1 = uuid.uuid4()
        s2 = uuid.uuid4()
        skills = {
            s1: self.MockSkill(s1, "SKILL-SQL-01", "SQL Tuning"),
            s2: self.MockSkill(s2, "SKILL-ALGO-01", "Dynamic Programming"),
        }
        mastery = {
            s1: self.MockMastery(s1, 1.0),
            s2: self.MockMastery(s2, 0.90),
        }
        res = DeterministicReadinessEngine.evaluate_career_readiness(
            target_role="Senior Systems Engineer",
            required_skill_ids=[s1, s2],
            skills_by_id=skills,
            mastery_by_skill_id=mastery,
            verified_project_skill_ids=[s1],
        )
        assert res["readiness_score"] == 0.95
        assert res["matching_skills_count"] == 2
        assert len(res["target_gap_analysis"]["deficit_skills"]) == 0
        assert res["target_gap_analysis"]["skills_breakdown"][0]["has_verified_project"] is True

    def test_missing_evidence_distinguished_from_zero(self):
        s1 = uuid.uuid4()
        s2 = uuid.uuid4()
        skills = {
            s1: self.MockSkill(s1, "SKILL-SQL-01", "SQL Tuning"),
            s2: self.MockSkill(s2, "SKILL-K8S-01", "Kubernetes Orchestration"),
        }
        # Only s1 has a persisted mastery record; s2 has zero evidence
        mastery = {
            s1: self.MockMastery(s1, 0.80),
        }
        res = DeterministicReadinessEngine.evaluate_career_readiness(
            target_role="DevOps Specialist",
            required_skill_ids=[s1, s2],
            skills_by_id=skills,
            mastery_by_skill_id=mastery,
            verified_project_skill_ids=[],
        )
        # s1: 0.80 (MET), s2: 0.0 (MISSING_EVIDENCE) -> mean = 0.40
        assert res["readiness_score"] == 0.40
        assert res["matching_skills_count"] == 1
        assert "SKILL-K8S-01" in res["target_gap_analysis"]["deficit_skills"]

        breakdown = res["target_gap_analysis"]["skills_breakdown"]
        k8s_item = next(b for b in breakdown if b["code"] == "SKILL-K8S-01")
        assert k8s_item["status"] == "MISSING_EVIDENCE"
        assert "No assessed or verified" in k8s_item["gap_note"]

    def test_decay_factor_reduces_readiness(self):
        s1 = uuid.uuid4()
        skills = {s1: self.MockSkill(s1, "SKILL-RUST", "Rust Concurrency")}
        # Raw score 1.0, decayed by 50% = 0.50 -> PARTIAL status
        mastery = {s1: self.MockMastery(s1, score=1.0, decay=0.50)}
        res = DeterministicReadinessEngine.evaluate_career_readiness(
            target_role="Rust Systems Developer",
            required_skill_ids=[s1],
            skills_by_id=skills,
            mastery_by_skill_id=mastery,
            verified_project_skill_ids=[],
        )
        assert res["readiness_score"] == 0.50
        assert res["matching_skills_count"] == 0
        assert "SKILL-RUST" in res["target_gap_analysis"]["partial_skills"]


# =============================================================================
# 2. INTEGRATION TESTS: SERVICE LAYER
# =============================================================================
@pytest.mark.asyncio
class TestPlacementServiceIntegration:
    async def test_project_studio_lifecycle(self, db_session: AsyncSession, seed_data: dict):
        inst = seed_data["inst1"]
        student = seed_data["student_user"]
        faculty = seed_data["faculty_user"]
        other_student = seed_data["inst_admin"]
        service = PlacementService(db_session)

        # 1. Student creates project
        project = await service.create_project(
            institution_id=inst.id,
            student_user_id=student.id,
            title="Distributed Key-Value Store",
            description="LSM-Tree with write-ahead logging and bloom filters.",
            project_type="CAPSTONE",
            repository_url="https://github.com/student/lsm-kv",
        )
        assert project.status == "DRAFT"
        assert project.title == "Distributed Key-Value Store"

        # 2. Student updates project fields
        updated = await service.update_project(
            institution_id=inst.id,
            project_id=project.id,
            user_id=student.id,
            deployment_url="https://demo.dhruva.ai/lsm",
        )
        assert updated.deployment_url == "https://demo.dhruva.ai/lsm"

        # 3. Cross-student edit prohibited
        with pytest.raises(PermissionDeniedError):
            await service.update_project(
                institution_id=inst.id,
                project_id=project.id,
                user_id=other_student.id,
                title="Malicious Rename",
            )

        # 4. Student submits project
        submitted = await service.submit_project(
            institution_id=inst.id,
            project_id=project.id,
            student_user_id=student.id,
        )
        assert submitted.status == "SUBMITTED"

        # 5. Faculty verifies project
        verified = await service.verify_project(
            institution_id=inst.id,
            project_id=project.id,
            verifier_user_id=faculty.id,
            is_verified=True,
            verification_notes="Comprehensive LSM compaction implementation and benchmarks verified.",
        )
        assert verified.status == "VERIFIED"
        assert verified.verified_by == faculty.id
        assert verified.verified_at is not None

        # 6. Editing verified project is blocked
        with pytest.raises(ConflictError):
            await service.update_project(
                institution_id=inst.id,
                project_id=project.id,
                user_id=student.id,
                title="Altered Title After Approval",
            )

        # 7. Faculty revokes verified project
        revoked = await service.revoke_project_verification(
            institution_id=inst.id,
            project_id=project.id,
            revoker_user_id=faculty.id,
            revocation_reason="Plagiarism detected in external benchmark library.",
        )
        assert revoked.status == "REVOKED"
        assert revoked.revoked_by == faculty.id
        assert "Plagiarism detected" in revoked.revocation_reason

    async def test_portfolio_privacy_and_publication(self, db_session: AsyncSession, seed_data: dict):
        inst = seed_data["inst1"]
        student = seed_data["student_user"]
        faculty = seed_data["faculty_user"]
        service = PlacementService(db_session)

        # 1. Get or create portfolio
        portfolio = await service.get_or_create_portfolio(inst.id, student)
        assert portfolio.visibility == "PRIVATE"
        assert portfolio.is_published is False

        # 2. Create and verify a project to curate
        project = await service.create_project(
            institution_id=inst.id,
            student_user_id=student.id,
            title="Consensus Raft Node",
            project_type="COURSE_PROJECT",
        )
        await service.submit_project(inst.id, project.id, student.id)
        await service.verify_project(inst.id, project.id, faculty.id, True, "Approved")

        # 3. Update portfolio
        await service.update_portfolio(
            institution_id=inst.id,
            student_user_id=student.id,
            headline="Distributed Systems Researcher",
            bio="CS student specializing in fault-tolerant algorithms.",
            visibility="PUBLIC",
            curated_project_ids=[str(project.id)],
            social_links={"github": "https://github.com/student"},
        )

        # 4. Attempt to view before publication -> fails for unauthorized viewer
        with pytest.raises(PermissionDeniedError):
            await service.get_portfolio_by_slug(inst.id, portfolio.slug, viewer_user=None)

        # 5. Publish portfolio
        await service.publish_portfolio(inst.id, student.id, publish=True)

        # 6. Now public viewer can access published public portfolio
        view = await service.get_portfolio_by_slug(inst.id, portfolio.slug, viewer_user=None)
        assert view["headline"] == "Distributed Systems Researcher"
        assert len(view["curated_projects"]) == 1
        assert view["curated_projects"][0]["title"] == "Consensus Raft Node"

    async def test_career_goal_and_deterministic_readiness(self, db_session: AsyncSession, seed_data: dict):
        inst = seed_data["inst1"]
        student = seed_data["student_user"]
        service = PlacementService(db_session)

        # 1. Create institutional skills
        skill1 = Skill(
            id=uuid.uuid4(),
            institution_id=inst.id,
            code="SKILL-SYS-01",
            name="Linux Kernel Concurrency",
            category="SYSTEMS",
        )
        skill2 = Skill(
            id=uuid.uuid4(),
            institution_id=inst.id,
            code="SKILL-NET-01",
            name="Socket Programming",
            category="NETWORKS",
        )
        db_session.add_all([skill1, skill2])
        await db_session.commit()

        # 2. Add MasteryRecord for skill1
        m1 = MasteryRecord(
            id=uuid.uuid4(),
            institution_id=inst.id,
            student_user_id=student.id,
            skill_id=skill1.id,
            mastery_score=0.90,
            confidence_score=0.95,
            competency_level="MASTERY",
            assessment_count=2,
            evidence_count=1,
            decay_factor=1.0,
            rule_version="2026.1",
            calculation_provenance={},
            is_stale=False,
            last_assessed_at=utc_now(),
        )
        db_session.add(m1)
        await db_session.commit()

        # 3. Student sets career goal
        goal = await service.create_or_update_career_goal(
            institution_id=inst.id,
            student_user_id=student.id,
            target_role="Systems Software Engineer",
            target_industry="Infrastructure",
            target_companies=["Google", "Cloudflare"],
            required_skill_ids=[str(skill1.id), str(skill2.id)],
        )
        assert goal.target_role == "Systems Software Engineer"

        # 4. Compute readiness: skill1 is 0.90 (MET), skill2 is missing evidence (0.0) -> (0.90 + 0) / 2 = 0.45
        readiness = await service.compute_career_readiness(inst.id, student.id, goal.id)
        assert readiness.readiness_score == 0.45
        assert readiness.matching_skills_count == 1
        assert readiness.total_required_skills == 2
        assert "SKILL-NET-01" in readiness.target_gap_analysis["deficit_skills"]
        assert readiness.rule_version == "2026.1"


# =============================================================================
# 3. HTTP API END-TO-END TESTS
# =============================================================================
@pytest.mark.asyncio
class TestPlacementApiEndpoints:
    def _auth_headers(self, user: User) -> dict:
        token = create_access_token(
            subject=str(user.id),
            claims={"institution_id": str(user.institution_id) if user.institution_id else None},
        )
        return {"Authorization": f"Bearer {token}"}

    async def test_project_api_crud_and_verification(self, client: AsyncClient, seed_data: dict):
        inst = seed_data["inst1"]
        student = seed_data["student_user"]
        admin = seed_data["inst_admin"]
        student_headers = self._auth_headers(student)
        admin_headers = self._auth_headers(admin)

        # 1. Create project
        create_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/projects",
            headers=student_headers,
            json={
                "title": "Compiler Frontend Parser",
                "description": "Recursive descent AST generator.",
                "project_type": "COURSE_PROJECT",
                "repository_url": "https://github.com/student/ast-parser",
            },
        )
        assert create_resp.status_code == 201
        project_id = create_resp.json()["data"]["id"]

        # 2. Submit project
        sub_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/projects/{project_id}/submit",
            headers=student_headers,
        )
        assert sub_resp.status_code == 200
        assert sub_resp.json()["data"]["status"] == "SUBMITTED"

        # 3. Admin verifies project
        verify_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/projects/{project_id}/verify",
            headers=admin_headers,
            json={
                "is_verified": True,
                "verification_notes": "AST parser generates correct tokens and intermediate representations.",
            },
        )
        assert verify_resp.status_code == 200
        assert verify_resp.json()["data"]["status"] == "VERIFIED"

    async def test_portfolio_lifecycle_api(self, client: AsyncClient, seed_data: dict):
        inst = seed_data["inst1"]
        student = seed_data["student_user"]
        student_headers = self._auth_headers(student)

        # 1. Get my portfolio
        port_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/portfolios/me",
            headers=student_headers,
        )
        assert port_resp.status_code == 200
        slug = port_resp.json()["data"]["slug"]

        # 2. Update portfolio
        update_resp = await client.put(
            f"/api/v1/institutions/{inst.slug}/portfolios/me",
            headers=student_headers,
            json={
                "headline": "Systems Engineer & Compiler Enthusiast",
                "bio": "Building scalable database engines and parsers.",
                "visibility": "PUBLIC",
            },
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["data"]["visibility"] == "PUBLIC"

        # 3. Publish portfolio
        pub_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/portfolios/me/publish",
            headers=student_headers,
            json={"is_published": True},
        )
        assert pub_resp.status_code == 200
        assert pub_resp.json()["data"]["is_published"] is True

        # 4. View portfolio by slug
        view_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/portfolios/{slug}",
            headers=student_headers,
        )
        assert view_resp.status_code == 200
        assert view_resp.json()["data"]["headline"] == "Systems Engineer & Compiler Enthusiast"

    async def test_placement_talent_pool_rbac_and_isolation(self, client: AsyncClient, seed_data: dict):
        inst1 = seed_data["inst1"]
        inst2 = seed_data["inst2"]
        admin1 = seed_data["inst_admin"]
        student1 = seed_data["student_user"]
        user2 = seed_data["inst2_user"]

        admin1_headers = self._auth_headers(admin1)
        student1_headers = self._auth_headers(student1)
        user2_headers = self._auth_headers(user2)

        # 1. Student attempting talent search -> 403 Forbidden
        denied_resp = await client.get(
            f"/api/v1/institutions/{inst1.slug}/placement/talent-pool",
            headers=student1_headers,
        )
        assert denied_resp.status_code == 403

        # 2. Staff from Tenant 2 accessing Tenant 1 talent pool -> 403 Forbidden
        cross_resp = await client.get(
            f"/api/v1/institutions/{inst1.slug}/placement/talent-pool",
            headers=user2_headers,
        )
        assert cross_resp.status_code == 403

        # 3. Authorized Admin searching talent pool
        pool_resp = await client.get(
            f"/api/v1/institutions/{inst1.slug}/placement/talent-pool",
            headers=admin1_headers,
        )
        assert pool_resp.status_code == 200
        assert isinstance(pool_resp.json()["data"], list)

        # 4. Placement analytics
        analytics_resp = await client.get(
            f"/api/v1/institutions/{inst1.slug}/placement/readiness-analytics",
            headers=admin1_headers,
        )
        assert analytics_resp.status_code == 200
        data = analytics_resp.json()["data"]
        assert "total_evaluated_students" in data
        assert "distribution" in data
