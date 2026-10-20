"""Dhruva.AI V2 — Institutional Analytics & Academic Interventions Application Service.

Coordinates:
- Real-time and pre-computed analytical rollups (Institutional & Departmental).
- Early Warning risk detection across student cohort.
- Academic Intervention lifecycle (ASSIGNED -> IN_PROGRESS -> COMPLETED | ESCALATED | DISMISSED).
- Notification dispatch on intervention triggers and completions.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.analytics.early_warning_engine import DeterministicEarlyWarningEngine
from src.application.analytics.notification_service import NotificationService
from src.core.errors import ConflictError, NotFoundError, PermissionDeniedError, ValidationError
from src.domain.academic.models import Course, CourseOffering, Department, StudentEnrollment, StudentProfile
from src.domain.assessment.models import Assessment, AssessmentResult, AssessmentSubmission
from src.domain.identity.models import User
from src.domain.mastery.models import MasteryRecord, Skill
from src.domain.placement.models import Project
from src.domain.analytics.models import AnalyticsRollup, Intervention
from src.infrastructure.persistence.postgres.base import utc_now


class AnalyticsService:
    """Application service for institutional analytics rollups and academic interventions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # 1. ANALYTICS ROLLUPS (PRE-COMPUTED & REAL-TIME OLTP)
    # =========================================================================
    async def compute_institutional_rollups(self, institution_id: uuid.UUID) -> AnalyticsRollup:
        """Compute institutional executive health rollups directly from live database tables."""
        # 1. Total Students
        student_count_stmt = select(func.count(StudentProfile.id)).where(StudentProfile.institution_id == institution_id)
        total_students = (await self.session.execute(student_count_stmt)).scalar_one() or 0

        # 2. Total Faculty / Users
        user_count_stmt = select(func.count(User.id)).where(User.institution_id == institution_id)
        total_users = (await self.session.execute(user_count_stmt)).scalar_one() or 0

        # 3. Active Course Offerings
        offering_stmt = select(func.count(CourseOffering.id)).where(CourseOffering.institution_id == institution_id)
        total_offerings = (await self.session.execute(offering_stmt)).scalar_one() or 0

        # 4. Total Assessments & Average Pass Rate
        res_stmt = select(AssessmentResult).where(AssessmentResult.institution_id == institution_id)
        results = list((await self.session.execute(res_stmt)).scalars().all())
        total_graded = len(results)
        passed_count = sum(1 for r in results if r.is_passed)
        avg_pass_rate = (passed_count / total_graded) if total_graded > 0 else 1.0
        avg_assessment_pct = (sum(r.percentage for r in results) / total_graded) if total_graded > 0 else 0.0

        # 5. Mastery Competency Averages
        mastery_stmt = select(MasteryRecord).where(MasteryRecord.institution_id == institution_id)
        mastery_records = list((await self.session.execute(mastery_stmt)).scalars().all())
        total_mastery = len(mastery_records)
        avg_mastery_score = (sum(m.mastery_score for m in mastery_records) / total_mastery) if total_mastery > 0 else 0.0

        # 6. Verified Projects Count
        proj_stmt = select(func.count(Project.id)).where(
            and_(
                Project.institution_id == institution_id,
                Project.status == "VERIFIED",
            )
        )
        verified_projects = (await self.session.execute(proj_stmt)).scalar_one() or 0

        # 7. Open Interventions Count
        interv_stmt = select(func.count(Intervention.id)).where(
            and_(
                Intervention.institution_id == institution_id,
                Intervention.status.in_(["ASSIGNED", "IN_PROGRESS", "ESCALATED"]),
            )
        )
        active_interventions = (await self.session.execute(interv_stmt)).scalar_one() or 0

        metrics = {
            "total_students": total_students,
            "total_users": total_users,
            "active_course_offerings": total_offerings,
            "total_graded_assessments": total_graded,
            "overall_passing_rate": round(avg_pass_rate, 3),
            "average_assessment_percentage": round(avg_assessment_pct, 1),
            "average_skill_mastery": round(avg_mastery_score, 3),
            "verified_projects_count": verified_projects,
            "active_interventions_count": active_interventions,
            "evaluated_at": utc_now().isoformat(),
        }

        # Store or update institutional rollup
        stmt = select(AnalyticsRollup).where(
            and_(
                AnalyticsRollup.institution_id == institution_id,
                AnalyticsRollup.department_id == None,
                AnalyticsRollup.rollup_type == "INSTITUTIONAL_SUMMARY",
            )
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()

        now = utc_now()
        if existing:
            existing.metrics_payload = metrics
            existing.computed_at = now
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        rollup = AnalyticsRollup(
            id=uuid.uuid4(),
            institution_id=institution_id,
            department_id=None,
            rollup_type="INSTITUTIONAL_SUMMARY",
            metrics_payload=metrics,
            computed_at=now,
        )
        self.session.add(rollup)
        await self.session.commit()
        await self.session.refresh(rollup)
        return rollup

    async def compute_departmental_rollups(
        self, institution_id: uuid.UUID, department_id: uuid.UUID
    ) -> AnalyticsRollup:
        """Compute departmental metrics rollups for HOD executive views."""
        # 1. Total Courses in Dept
        c_stmt = select(func.count(Course.id)).where(
            and_(
                Course.institution_id == institution_id,
                Course.department_id == department_id,
            )
        )
        course_count = (await self.session.execute(c_stmt)).scalar_one() or 0

        # 2. Offerings in Department
        off_stmt = (
            select(CourseOffering.id)
            .join(Course, Course.id == CourseOffering.course_id)
            .where(
                and_(
                    CourseOffering.institution_id == institution_id,
                    Course.department_id == department_id,
                )
            )
        )
        off_ids = list((await self.session.execute(off_stmt)).scalars().all())
        total_offerings = len(off_ids)

        # 3. Departmental Assessment Results
        if off_ids:
            res_stmt = (
                select(AssessmentResult)
                .join(AssessmentSubmission, AssessmentSubmission.id == AssessmentResult.submission_id)
                .join(Assessment, Assessment.id == AssessmentSubmission.assessment_id)
                .where(
                    and_(
                        AssessmentResult.institution_id == institution_id,
                        Assessment.course_offering_id.in_(off_ids),
                    )
                )
            )
            results = list((await self.session.execute(res_stmt)).scalars().all())
        else:
            results = []

        total_graded = len(results)
        passed_count = sum(1 for r in results if r.is_passed)
        pass_rate = (passed_count / total_graded) if total_graded > 0 else 1.0
        avg_pct = (sum(r.percentage for r in results) / total_graded) if total_graded > 0 else 0.0

        # 4. Department Interventions
        int_stmt = select(func.count(Intervention.id)).where(
            and_(
                Intervention.institution_id == institution_id,
                Intervention.status.in_(["ASSIGNED", "IN_PROGRESS"]),
            )
        )
        open_interventions = (await self.session.execute(int_stmt)).scalar_one() or 0

        metrics = {
            "department_id": str(department_id),
            "total_courses": course_count,
            "active_course_offerings": total_offerings,
            "total_graded_assessments": total_graded,
            "department_passing_rate": round(pass_rate, 3),
            "department_average_score": round(avg_pct, 1),
            "open_interventions_count": open_interventions,
            "evaluated_at": utc_now().isoformat(),
        }

        # Store or update departmental rollup
        stmt = select(AnalyticsRollup).where(
            and_(
                AnalyticsRollup.institution_id == institution_id,
                AnalyticsRollup.department_id == department_id,
                AnalyticsRollup.rollup_type == "DEPARTMENTAL_HEALTH",
            )
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()

        now = utc_now()
        if existing:
            existing.metrics_payload = metrics
            existing.computed_at = now
            await self.session.commit()
            await self.session.refresh(existing)
            return existing

        rollup = AnalyticsRollup(
            id=uuid.uuid4(),
            institution_id=institution_id,
            department_id=department_id,
            rollup_type="DEPARTMENTAL_HEALTH",
            metrics_payload=metrics,
            computed_at=now,
        )
        self.session.add(rollup)
        await self.session.commit()
        await self.session.refresh(rollup)
        return rollup

    async def get_institutional_analytics(self, institution_id: uuid.UUID) -> Dict[str, Any]:
        """Fetch latest cached institutional rollup or compute on demand (< 150ms)."""
        stmt = (
            select(AnalyticsRollup)
            .where(
                and_(
                    AnalyticsRollup.institution_id == institution_id,
                    AnalyticsRollup.department_id == None,
                    AnalyticsRollup.rollup_type == "INSTITUTIONAL_SUMMARY",
                )
            )
            .order_by(AnalyticsRollup.computed_at.desc())
        )
        rollup = (await self.session.execute(stmt)).scalar_one_or_none()
        if not rollup:
            rollup = await self.compute_institutional_rollups(institution_id)

        return {
            "id": str(rollup.id),
            "institution_id": str(rollup.institution_id),
            "rollup_type": rollup.rollup_type,
            "computed_at": rollup.computed_at.isoformat(),
            "metrics": rollup.metrics_payload,
        }

    async def get_departmental_analytics(
        self, institution_id: uuid.UUID, department_id: uuid.UUID
    ) -> Dict[str, Any]:
        """Fetch latest cached departmental rollup or compute on demand."""
        stmt = (
            select(AnalyticsRollup)
            .where(
                and_(
                    AnalyticsRollup.institution_id == institution_id,
                    AnalyticsRollup.department_id == department_id,
                    AnalyticsRollup.rollup_type == "DEPARTMENTAL_HEALTH",
                )
            )
            .order_by(AnalyticsRollup.computed_at.desc())
        )
        rollup = (await self.session.execute(stmt)).scalar_one_or_none()
        if not rollup:
            rollup = await self.compute_departmental_rollups(institution_id, department_id)

        return {
            "id": str(rollup.id),
            "institution_id": str(rollup.institution_id),
            "department_id": str(rollup.department_id),
            "rollup_type": rollup.rollup_type,
            "computed_at": rollup.computed_at.isoformat(),
            "metrics": rollup.metrics_payload,
        }

    # =========================================================================
    # 2. EARLY WARNING & AT-RISK DETECTION
    # =========================================================================
    async def detect_at_risk_students(self, institution_id: uuid.UUID) -> List[Dict[str, Any]]:
        """Scans all institutional students using DeterministicEarlyWarningEngine."""
        # 1. Fetch students
        stud_stmt = (
            select(StudentProfile, User)
            .join(User, User.id == StudentProfile.user_id)
            .where(StudentProfile.institution_id == institution_id)
        )
        res = await self.session.execute(stud_stmt)
        students_with_users = list(res.all())

        at_risk_list: List[Dict[str, Any]] = []

        for student, user in students_with_users:
            # Fetch student's assessment results
            res_stmt = (
                select(AssessmentResult)
                .join(AssessmentSubmission, AssessmentSubmission.id == AssessmentResult.submission_id)
                .where(
                    and_(
                        AssessmentSubmission.student_user_id == user.id,
                        AssessmentResult.institution_id == institution_id,
                    )
                )
            )
            results = list((await self.session.execute(res_stmt)).scalars().all())

            # Fetch student's mastery records
            m_stmt = (
                select(MasteryRecord)
                .options(selectinload(MasteryRecord.skill))
                .where(
                    and_(
                        MasteryRecord.student_user_id == user.id,
                        MasteryRecord.institution_id == institution_id,
                    )
                )
            )
            mastery = list((await self.session.execute(m_stmt)).scalars().all())

            # Open interventions count
            int_count_stmt = select(func.count(Intervention.id)).where(
                and_(
                    Intervention.student_user_id == user.id,
                    Intervention.institution_id == institution_id,
                    Intervention.status.in_(["ASSIGNED", "IN_PROGRESS"]),
                )
            )
            open_int = (await self.session.execute(int_count_stmt)).scalar_one() or 0

            # Evaluate risk
            eval_res = DeterministicEarlyWarningEngine.evaluate_student_risk(
                student_user_id=user.id,
                graded_results=results,
                mastery_records=mastery,
                open_interventions_count=open_int,
            )

            if eval_res["is_at_risk"]:
                at_risk_list.append({
                    "student_id": str(user.id),
                    "full_name": f"{user.first_name} {user.last_name}",
                    "email": user.email,
                    "roll_number": student.roll_number,
                    "risk_level": eval_res["risk_level"],
                    "detected_rules": eval_res["detected_rules"],
                    "recommended_intervention_type": eval_res["recommended_intervention_type"],
                    "trigger_reason": eval_res["trigger_reason"],
                    "metrics_summary": eval_res["metrics_summary"],
                })

        return at_risk_list

    # =========================================================================
    # 3. INTERVENTIONS MANAGEMENT
    # =========================================================================
    async def create_intervention(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
        faculty_user_id: Optional[uuid.UUID],
        intervention_type: str,
        trigger_reason: str,
        action_plan: str = "",
        notes: str = "",
        due_date: Optional[datetime] = None,
    ) -> Intervention:
        """Create and assign an academic intervention to a student."""
        if not trigger_reason or len(trigger_reason.strip()) < 5:
            raise ValidationError("A documented trigger reason (minimum 5 characters) is required.")

        intervention = Intervention(
            id=uuid.uuid4(),
            institution_id=institution_id,
            student_user_id=student_user_id,
            faculty_user_id=faculty_user_id,
            intervention_type=intervention_type.upper().strip(),
            trigger_reason=trigger_reason.strip(),
            status="ASSIGNED",
            action_plan=action_plan.strip(),
            notes=notes.strip(),
            assigned_at=utc_now(),
            due_date=due_date,
        )
        self.session.add(intervention)
        await self.session.commit()
        await self.session.refresh(intervention)

        # Dispatch in-app notification to the student
        notif_service = NotificationService(self.session)
        await notif_service.create_notification(
            institution_id=institution_id,
            recipient_user_id=student_user_id,
            notification_type="INTERVENTION_ASSIGNED",
            title=f"Academic Support Assigned: {intervention.intervention_type.replace('_', ' ')}",
            message=f"An academic intervention has been assigned to support your progress: {trigger_reason}",
            actor_user_id=faculty_user_id,
            link_url="/workspace/analytics",
            metadata_json={"intervention_id": str(intervention.id)},
        )

        return intervention

    async def update_intervention_status(
        self,
        institution_id: uuid.UUID,
        intervention_id: uuid.UUID,
        user_id: uuid.UUID,
        status: str,
        outcome_notes: Optional[str] = None,
        action_plan: Optional[str] = None,
    ) -> Intervention:
        """Update intervention status and log outcome notes."""
        valid_statuses = {"ASSIGNED", "IN_PROGRESS", "COMPLETED", "ESCALATED", "DISMISSED"}
        new_status = status.upper().strip()
        if new_status not in valid_statuses:
            raise ValidationError(f"Invalid status '{status}'. Valid: {sorted(valid_statuses)}")

        stmt = select(Intervention).where(
            and_(
                Intervention.id == intervention_id,
                Intervention.institution_id == institution_id,
            )
        )
        intervention = (await self.session.execute(stmt)).scalar_one_or_none()
        if not intervention:
            raise NotFoundError(f"Intervention '{intervention_id}' not found.")

        intervention.status = new_status
        if outcome_notes is not None:
            intervention.outcome_notes = outcome_notes.strip()
        if action_plan is not None:
            intervention.action_plan = action_plan.strip()

        if new_status == "COMPLETED":
            intervention.completed_at = utc_now()
            # Notify student of completion
            notif_service = NotificationService(self.session)
            await notif_service.create_notification(
                institution_id=institution_id,
                recipient_user_id=intervention.student_user_id,
                notification_type="INTERVENTION_COMPLETED",
                title=f"Intervention Completed: {intervention.intervention_type.replace('_', ' ')}",
                message="Your assigned academic intervention has been marked completed by faculty.",
                actor_user_id=user_id,
                link_url="/workspace/analytics",
                metadata_json={"intervention_id": str(intervention.id)},
            )

        await self.session.commit()
        await self.session.refresh(intervention)
        return intervention

    async def list_interventions(
        self,
        institution_id: uuid.UUID,
        student_user_id: Optional[uuid.UUID] = None,
        faculty_user_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Intervention]:
        """List interventions with filtering."""
        stmt = (
            select(Intervention)
            .options(
                selectinload(Intervention.student),
                selectinload(Intervention.faculty),
            )
            .where(Intervention.institution_id == institution_id)
        )
        if student_user_id:
            stmt = stmt.where(Intervention.student_user_id == student_user_id)
        if faculty_user_id:
            stmt = stmt.where(Intervention.faculty_user_id == faculty_user_id)
        if status:
            stmt = stmt.where(Intervention.status == status.upper().strip())

        stmt = stmt.order_by(Intervention.assigned_at.desc()).limit(limit).offset(offset)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_intervention(
        self, institution_id: uuid.UUID, intervention_id: uuid.UUID
    ) -> Intervention:
        """Fetch single intervention with strict tenant scoping."""
        stmt = (
            select(Intervention)
            .options(
                selectinload(Intervention.student),
                selectinload(Intervention.faculty),
            )
            .where(
                and_(
                    Intervention.id == intervention_id,
                    Intervention.institution_id == institution_id,
                )
            )
        )
        intervention = (await self.session.execute(stmt)).scalar_one_or_none()
        if not intervention:
            raise NotFoundError(f"Intervention '{intervention_id}' not found.")
        return intervention
