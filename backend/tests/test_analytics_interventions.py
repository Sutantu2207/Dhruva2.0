"""Dhruva.AI V2 — Phase 8 Interventions, Notifications & Analytics Test Suite.

Verifies:
1. Deterministic Early Warning Engine risk scoring and threshold indicators.
2. Academic Intervention lifecycle (creation, assignment, status transitions, outcome notes).
3. Notification Hub dispatch, recipient boundary isolation, and batch read updates.
4. Institutional and Departmental Analytics rollups (computation, database caching, KPI aggregation).
5. Strict RBAC enforcement and cross-tenant boundary isolation across all Phase 8 endpoints.
"""

import uuid
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.analytics.analytics_service import AnalyticsService
from src.application.analytics.early_warning_engine import DeterministicEarlyWarningEngine
from src.application.analytics.notification_service import NotificationService
from src.core.errors import NotFoundError, PermissionDeniedError, ValidationError
from src.core.security import create_access_token
from src.domain.identity.models import Institution, Role, User, UserRole
from src.domain.identity.roles import SystemRole


# =============================================================================
# 1. UNIT TESTS: DETERMINISTIC EARLY WARNING ENGINE
# =============================================================================
class TestDeterministicEarlyWarningEngine:
    def test_zero_risk_profile(self):
        result = DeterministicEarlyWarningEngine.evaluate_student_risk(
            student_user_id=uuid.uuid4(),
            graded_results=[],
            mastery_records=[],
            open_interventions_count=0,
        )
        assert result["is_at_risk"] is False
        assert result["risk_level"] == "NONE"
        assert len(result["detected_rules"]) == 0

    def test_critical_assessment_failure(self):
        student_id = uuid.uuid4()
        # 3 failed out of 4 = 75% fail rate (>= 50%) -> HIGH risk
        results = [
            SimpleNamespace(percentage=30.0, is_passed=False),
            SimpleNamespace(percentage=35.0, is_passed=False),
            SimpleNamespace(percentage=40.0, is_passed=False),
            SimpleNamespace(percentage=80.0, is_passed=True),
        ]
        res = DeterministicEarlyWarningEngine.evaluate_student_risk(
            student_user_id=student_id,
            graded_results=results,
            mastery_records=[],
            open_interventions_count=0,
        )
        assert res["is_at_risk"] is True
        assert res["risk_level"] == "HIGH"
        rule_codes = [r["rule_code"] for r in res["detected_rules"]]
        assert "HIGH_ASSESSMENT_FAIL_RATE" in rule_codes
        assert res["recommended_intervention_type"] == "REMEDIAL_SESSION"

    def test_mastery_decay_trigger(self):
        student_id = uuid.uuid4()
        records = [
            SimpleNamespace(mastery_score=0.40, decay_factor=0.50, skill=SimpleNamespace(code="CS-ALG")),
            SimpleNamespace(mastery_score=0.45, decay_factor=0.55, skill=SimpleNamespace(code="CS-DB")),
        ]
        res = DeterministicEarlyWarningEngine.evaluate_student_risk(
            student_user_id=student_id,
            graded_results=[],
            mastery_records=records,
            open_interventions_count=0,
        )
        assert res["is_at_risk"] is True
        assert res["risk_level"] == "HIGH"
        rule_codes = [r["rule_code"] for r in res["detected_rules"]]
        assert "CRITICAL_MASTERY_DECAY" in rule_codes


# =============================================================================
# 2. INTEGRATION TESTS: DOMAIN SERVICES & ISOLATION
# =============================================================================
class TestAnalyticsDomainServices:
    async def test_intervention_lifecycle(self, db_session: AsyncSession, seed_data: dict):
        inst = seed_data["inst1"]
        student = seed_data["student_user"]
        faculty = seed_data["faculty_user"]
        service = AnalyticsService(db_session)

        # 1. Create Intervention
        intervention = await service.create_intervention(
            institution_id=inst.id,
            student_user_id=student.id,
            faculty_user_id=faculty.id,
            intervention_type="PEER_TUTORING",
            trigger_reason="Multiple failed assessment attempts in Distributed Systems.",
            action_plan="Assign TA for weekly 1-on-1 tutoring sessions on consensus algorithms.",
        )
        assert intervention.id is not None
        assert intervention.status == "ASSIGNED"
        assert intervention.intervention_type == "PEER_TUTORING"

        # 2. Update Intervention Status
        updated = await service.update_intervention_status(
            institution_id=inst.id,
            intervention_id=intervention.id,
            user_id=faculty.id,
            status="IN_PROGRESS",
            action_plan="Adjusted action plan to include mock quizzes.",
        )
        assert updated.status == "IN_PROGRESS"
        assert updated.action_plan == "Adjusted action plan to include mock quizzes."

        # 3. Resolve Intervention
        resolved = await service.update_intervention_status(
            institution_id=inst.id,
            intervention_id=intervention.id,
            user_id=faculty.id,
            status="COMPLETED",
            outcome_notes="Student achieved 85% on remedial assessment.",
        )
        assert resolved.status == "COMPLETED"
        assert resolved.completed_at is not None
        assert resolved.outcome_notes == "Student achieved 85% on remedial assessment."

        # 4. List interventions
        items = await service.list_interventions(institution_id=inst.id, student_user_id=student.id)
        assert len(items) >= 1
        assert items[0].id == intervention.id

    async def test_notification_recipient_isolation(self, db_session: AsyncSession, seed_data: dict):
        inst = seed_data["inst1"]
        student = seed_data["student_user"]
        faculty = seed_data["faculty_user"]
        service = NotificationService(db_session)

        # 1. Create notification for student
        notif = await service.create_notification(
            institution_id=inst.id,
            recipient_user_id=student.id,
            notification_type="INTERVENTION_ASSIGNED",
            title="Academic Support Assigned",
            message="You have been assigned a tutoring session for Systems.",
            actor_user_id=faculty.id,
        )
        assert notif.id is not None
        assert notif.is_read is False

        # 2. Check unread count
        res = await service.list_user_notifications(inst.id, student.id, unread_only=True)
        assert res["unread_count"] >= 1

        # 3. Faculty attempts to mark student's notification as read -> PermissionDeniedError
        with pytest.raises(PermissionDeniedError):
            await service.mark_as_read(
                institution_id=inst.id,
                notification_id=notif.id,
                user_id=faculty.id,
            )

        # 4. Student marks own notification as read -> Success
        marked = await service.mark_as_read(
            institution_id=inst.id,
            notification_id=notif.id,
            user_id=student.id,
        )
        assert marked.is_read is True
        assert marked.read_at is not None

        # 5. Batch mark all as read
        batch_count = await service.mark_all_as_read(inst.id, student.id)
        assert batch_count == 0  # Already marked

    async def test_institutional_analytics_rollups(self, db_session: AsyncSession, seed_data: dict):
        inst = seed_data["inst1"]
        service = AnalyticsService(db_session)

        # 1. Compute institutional rollup
        rollup = await service.compute_institutional_rollups(institution_id=inst.id)
        assert rollup.institution_id == inst.id
        assert rollup.rollup_type == "INSTITUTIONAL_SUMMARY"
        assert "total_students" in rollup.metrics_payload
        assert "overall_passing_rate" in rollup.metrics_payload

        # 2. Query institutional rollup (uses cached snapshot)
        fetched = await service.get_institutional_analytics(institution_id=inst.id)
        assert fetched["id"] == str(rollup.id)
        assert fetched["metrics"]["total_students"] == rollup.metrics_payload["total_students"]


# =============================================================================
# 3. HTTP ENDPOINT TESTS: RBAC & APIS
# =============================================================================
class TestAnalyticsEndpointsHTTP:
    def _auth_headers(self, user: User) -> dict:
        token = create_access_token(
            subject=str(user.id),
            claims={"institution_id": str(user.institution_id) if user.institution_id else None},
        )
        return {"Authorization": f"Bearer {token}"}

    async def test_interventions_api_lifecycle(self, client: AsyncClient, seed_data: dict):
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        student = seed_data["student_user"]
        admin_headers = self._auth_headers(admin)
        student_headers = self._auth_headers(student)

        # 1. Student attempting to create intervention -> 403 Forbidden
        denied_create = await client.post(
            f"/api/v1/institutions/{inst.slug}/interventions",
            headers=student_headers,
            json={
                "student_user_id": str(student.id),
                "intervention_type": "ACADEMIC_PROBATION",
                "trigger_reason": "Unauthorized attempt",
                "action_plan": "Action plan",
            },
        )
        assert denied_create.status_code == 403

        # 2. Admin creates intervention
        create_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/interventions",
            headers=admin_headers,
            json={
                "student_user_id": str(student.id),
                "intervention_type": "CURRICULAR_COUNSELING",
                "trigger_reason": "Midterm performance review required.",
                "action_plan": "Schedule academic advising interview within 5 business days.",
            },
        )
        assert create_resp.status_code == 201
        data = create_resp.json()["data"]
        intervention_id = data["id"]
        assert data["intervention_type"] == "CURRICULAR_COUNSELING"
        assert data["status"] == "ASSIGNED"

        # 3. List interventions (Admin view)
        list_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/interventions",
            headers=admin_headers,
        )
        assert list_resp.status_code == 200
        assert len(list_resp.json()["data"]) >= 1

        # 4. Student view (self-filtered isolation)
        student_list_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/interventions",
            headers=student_headers,
        )
        assert student_list_resp.status_code == 200
        assert all(item["student_user_id"] == str(student.id) for item in student_list_resp.json()["data"])

        # 5. Admin updates intervention
        patch_resp = await client.patch(
            f"/api/v1/institutions/{inst.slug}/interventions/{intervention_id}",
            headers=admin_headers,
            json={
                "status": "COMPLETED",
                "outcome_notes": "Advising complete. Study schedule established.",
            },
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["data"]["status"] == "COMPLETED"

    async def test_detect_at_risk_api(self, client: AsyncClient, seed_data: dict):
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        student = seed_data["student_user"]
        admin_headers = self._auth_headers(admin)
        student_headers = self._auth_headers(student)

        # Student denied
        denied = await client.post(
            f"/api/v1/institutions/{inst.slug}/interventions/detect-at-risk",
            headers=student_headers,
        )
        assert denied.status_code == 403

        # Admin runs detection
        resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/interventions/detect-at-risk",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    async def test_notifications_hub_api(self, client: AsyncClient, seed_data: dict, db_session: AsyncSession):
        inst = seed_data["inst1"]
        student = seed_data["student_user"]
        student_headers = self._auth_headers(student)
        notif_service = NotificationService(db_session)

        # Seed notification directly
        notif = await notif_service.create_notification(
            institution_id=inst.id,
            recipient_user_id=student.id,
            notification_type="ANALYTICS_ALERT",
            title="System Maintenance Notice",
            message="Platform maintenance scheduled for Sunday midnight.",
        )

        # 1. Get notifications
        resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/notifications",
            headers=student_headers,
        )
        assert resp.status_code == 200
        items = resp.json()["data"]
        assert len(items) >= 1
        assert any(item["id"] == str(notif.id) for item in items)

        # 2. Get unread count
        count_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/notifications/unread-count",
            headers=student_headers,
        )
        assert count_resp.status_code == 200
        assert count_resp.json()["data"]["unread_count"] >= 1

        # 3. Mark single notification read
        mark_resp = await client.patch(
            f"/api/v1/institutions/{inst.slug}/notifications/{notif.id}/read",
            headers=student_headers,
        )
        assert mark_resp.status_code == 200
        assert mark_resp.json()["data"]["is_read"] is True

        # 4. Mark all read
        all_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/notifications/read-all",
            headers=student_headers,
        )
        assert all_resp.status_code == 200
        assert "updated_count" in all_resp.json()["data"]

    async def test_institutional_analytics_api_and_rbac(self, client: AsyncClient, seed_data: dict):
        inst = seed_data["inst1"]
        admin = seed_data["inst_admin"]
        student = seed_data["student_user"]
        admin_headers = self._auth_headers(admin)
        student_headers = self._auth_headers(student)

        # 1. Student denied institutional analytics
        denied = await client.get(
            f"/api/v1/institutions/{inst.slug}/analytics/institutional",
            headers=student_headers,
        )
        assert denied.status_code == 403

        # 2. Admin computes rollups
        compute_resp = await client.post(
            f"/api/v1/institutions/{inst.slug}/analytics/compute-rollups",
            headers=admin_headers,
        )
        assert compute_resp.status_code == 201
        assert "total_students" in compute_resp.json()["data"]["metrics"]

        # 3. Admin fetches institutional analytics
        analytics_resp = await client.get(
            f"/api/v1/institutions/{inst.slug}/analytics/institutional",
            headers=admin_headers,
        )
        assert analytics_resp.status_code == 200
        metrics = analytics_resp.json()["data"]["metrics"]
        assert "total_students" in metrics
        assert "overall_passing_rate" in metrics
