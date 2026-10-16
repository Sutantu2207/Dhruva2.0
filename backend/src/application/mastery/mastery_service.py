"""Dhruva.AI V2 — Mastery, Skills & Learning Evidence Application Service.

Coordinates:
- Concept & Skill Knowledge Graph management.
- Concept Prerequisites & Learning Outcomes.
- Learning Evidence submission & verification lifecycle.
- Deterministic mastery calculation with assessment synchronization.
- Spaced repetition scheduling via SuperMemo SM-2.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.mastery.mastery_engine import DeterministicMasteryEngine
from src.core.errors import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from src.domain.mastery.models import (
    Concept,
    ConceptPrerequisite,
    ConceptSkill,
    LearningEvidence,
    LearningOutcome,
    MasteryRecord,
    ReviewSchedule,
    Skill,
)
from src.domain.assessment.models import Assessment, AssessmentResult, AssessmentSubmission, Question
from src.infrastructure.persistence.postgres.base import utc_now


class MasteryService:
    """Application service for institutional knowledge graph, student mastery, and evidence verification."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # =========================================================================
    # CONCEPTS & PREREQUISITES
    # =========================================================================
    async def create_concept(
        self,
        institution_id: uuid.UUID,
        code: str,
        name: str,
        description: str = "",
        bloom_level: str = "UNDERSTAND",
        department_id: Optional[uuid.UUID] = None,
        course_id: Optional[uuid.UUID] = None,
        parent_concept_id: Optional[uuid.UUID] = None,
    ) -> Concept:
        stmt = select(Concept).where(
            Concept.institution_id == institution_id,
            Concept.code == code,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Concept with code '{code}' already exists in this institution.")

        concept = Concept(
            id=uuid.uuid4(),
            institution_id=institution_id,
            department_id=department_id,
            course_id=course_id,
            parent_concept_id=parent_concept_id,
            code=code,
            name=name,
            description=description,
            bloom_level=bloom_level,
        )
        self.session.add(concept)
        await self.session.commit()
        await self.session.refresh(concept)
        return concept

    async def list_concepts(
        self,
        institution_id: uuid.UUID,
        course_id: Optional[uuid.UUID] = None,
        department_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Concept]:
        stmt = (
            select(Concept)
            .where(Concept.institution_id == institution_id)
            .order_by(Concept.code.asc())
            .offset(offset)
            .limit(limit)
        )
        if course_id:
            stmt = stmt.where(Concept.course_id == course_id)
        if department_id:
            stmt = stmt.where(Concept.department_id == department_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_concept_prerequisite(
        self,
        institution_id: uuid.UUID,
        concept_id: uuid.UUID,
        prerequisite_concept_id: uuid.UUID,
    ) -> ConceptPrerequisite:
        if concept_id == prerequisite_concept_id:
            raise ValidationError("A concept cannot be a prerequisite of itself.")

        concept = await self.session.get(Concept, concept_id)
        if not concept or concept.institution_id != institution_id:
            raise NotFoundError("Concept not found in institution.")

        prereq = await self.session.get(Concept, prerequisite_concept_id)
        if not prereq or prereq.institution_id != institution_id:
            raise NotFoundError("Prerequisite concept not found in institution.")

        # Check existing
        stmt = select(ConceptPrerequisite).where(
            ConceptPrerequisite.concept_id == concept_id,
            ConceptPrerequisite.prerequisite_concept_id == prerequisite_concept_id,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        prereq_link = ConceptPrerequisite(
            id=uuid.uuid4(),
            institution_id=institution_id,
            concept_id=concept_id,
            prerequisite_concept_id=prerequisite_concept_id,
        )
        self.session.add(prereq_link)
        await self.session.commit()
        await self.session.refresh(prereq_link)
        return prereq_link

    async def list_concept_prerequisites(
        self,
        institution_id: uuid.UUID,
        concept_id: Optional[uuid.UUID] = None,
    ) -> List[ConceptPrerequisite]:
        stmt = (
            select(ConceptPrerequisite)
            .options(
                selectinload(ConceptPrerequisite.concept),
                selectinload(ConceptPrerequisite.prerequisite_concept),
            )
            .where(ConceptPrerequisite.institution_id == institution_id)
        )
        if concept_id:
            stmt = stmt.where(ConceptPrerequisite.concept_id == concept_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # LEARNING OUTCOMES
    # =========================================================================
    async def create_learning_outcome(
        self,
        institution_id: uuid.UUID,
        code: str,
        statement: str,
        bloom_level: str = "APPLY",
        course_id: Optional[uuid.UUID] = None,
        concept_id: Optional[uuid.UUID] = None,
        skill_id: Optional[uuid.UUID] = None,
    ) -> LearningOutcome:
        stmt = select(LearningOutcome).where(
            LearningOutcome.institution_id == institution_id,
            LearningOutcome.code == code,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Learning outcome with code '{code}' already exists.")

        outcome = LearningOutcome(
            id=uuid.uuid4(),
            institution_id=institution_id,
            course_id=course_id,
            code=code,
            statement=statement,
            bloom_level=bloom_level,
            concept_id=concept_id,
            skill_id=skill_id,
        )
        self.session.add(outcome)
        await self.session.commit()
        await self.session.refresh(outcome)
        return outcome

    async def list_learning_outcomes(
        self,
        institution_id: uuid.UUID,
        course_id: Optional[uuid.UUID] = None,
    ) -> List[LearningOutcome]:
        stmt = select(LearningOutcome).where(LearningOutcome.institution_id == institution_id)
        if course_id:
            stmt = stmt.where(LearningOutcome.course_id == course_id)
        stmt = stmt.order_by(LearningOutcome.code.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # SKILLS
    # =========================================================================
    async def create_skill(
        self,
        institution_id: uuid.UUID,
        code: str,
        name: str,
        category: str,
        description: str = "",
    ) -> Skill:
        stmt = select(Skill).where(
            Skill.institution_id == institution_id,
            Skill.code == code,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            raise ConflictError(f"Skill with code '{code}' already exists in this institution.")

        skill = Skill(
            id=uuid.uuid4(),
            institution_id=institution_id,
            code=code,
            name=name,
            category=category,
            description=description,
        )
        self.session.add(skill)
        await self.session.commit()
        await self.session.refresh(skill)
        return skill

    async def list_skills(
        self,
        institution_id: uuid.UUID,
        category: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Skill]:
        stmt = (
            select(Skill)
            .where(Skill.institution_id == institution_id)
            .order_by(Skill.category.asc(), Skill.code.asc())
            .offset(offset)
            .limit(limit)
        )
        if category:
            stmt = stmt.where(Skill.category == category)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def link_concept_to_skill(
        self,
        institution_id: uuid.UUID,
        concept_id: uuid.UUID,
        skill_id: uuid.UUID,
        weight: float = 1.0,
    ) -> ConceptSkill:
        concept = await self.session.get(Concept, concept_id)
        if not concept or concept.institution_id != institution_id:
            raise NotFoundError("Concept not found in institution.")

        skill = await self.session.get(Skill, skill_id)
        if not skill or skill.institution_id != institution_id:
            raise NotFoundError("Skill not found in institution.")

        stmt = select(ConceptSkill).where(
            ConceptSkill.concept_id == concept_id,
            ConceptSkill.skill_id == skill_id,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            existing.weight = weight
            await self.session.commit()
            return existing

        link = ConceptSkill(
            concept_id=concept_id,
            skill_id=skill_id,
            institution_id=institution_id,
            weight=weight,
        )
        self.session.add(link)
        await self.session.commit()
        return link

    # =========================================================================
    # LEARNING EVIDENCE WORKFLOW
    # =========================================================================
    async def submit_learning_evidence(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
        skill_id: uuid.UUID,
        evidence_type: str,
        title: str,
        artifact_url: str,
        description: str = "",
        concept_id: Optional[uuid.UUID] = None,
        file_size_bytes: Optional[int] = None,
    ) -> LearningEvidence:
        skill = await self.session.get(Skill, skill_id)
        if not skill or skill.institution_id != institution_id:
            raise NotFoundError("Skill not found in institution.")

        if concept_id:
            concept = await self.session.get(Concept, concept_id)
            if not concept or concept.institution_id != institution_id:
                raise NotFoundError("Concept not found in institution.")

        evidence = LearningEvidence(
            id=uuid.uuid4(),
            institution_id=institution_id,
            student_user_id=student_user_id,
            skill_id=skill_id,
            concept_id=concept_id,
            evidence_type=evidence_type,
            title=title,
            description=description,
            artifact_url=artifact_url,
            file_size_bytes=file_size_bytes,
            verification_status="PENDING",
            is_finalized=False,
            rule_version=DeterministicMasteryEngine.RULE_VERSION,
        )
        self.session.add(evidence)
        await self.session.commit()
        await self.session.refresh(evidence)
        return evidence

    async def verify_learning_evidence(
        self,
        institution_id: uuid.UUID,
        evidence_id: uuid.UUID,
        verifier_user_id: uuid.UUID,
        is_verified: bool,
        notes: str = "",
    ) -> LearningEvidence:
        evidence = await self.session.get(LearningEvidence, evidence_id)
        if not evidence or evidence.institution_id != institution_id:
            raise NotFoundError("Learning evidence not found in institution.")

        evidence.verification_status = "VERIFIED" if is_verified else "REJECTED"
        evidence.verified_by = verifier_user_id
        evidence.verified_at = utc_now()
        evidence.verification_notes = notes
        evidence.is_finalized = is_verified

        # Recalculate student mastery for this skill deterministically
        await self.session.commit()
        await self.recalculate_student_skill_mastery(
            institution_id=institution_id,
            student_user_id=evidence.student_user_id,
            skill_id=evidence.skill_id,
        )
        await self.session.refresh(evidence)
        return evidence

    # =========================================================================
    # ASSESSMENT TO EVIDENCE SYNCHRONIZATION
    # =========================================================================
    async def sync_evidence_from_assessment_result(
        self,
        institution_id: uuid.UUID,
        result_id: uuid.UUID,
    ) -> List[LearningEvidence]:
        """Idempotently create and synchronize learning evidence records from a finalized assessment result."""
        stmt = (
            select(AssessmentResult)
            .options(
                selectinload(AssessmentResult.submission).selectinload(
                    AssessmentSubmission.assessment
                )
            )
            .where(
                AssessmentResult.id == result_id,
                AssessmentResult.institution_id == institution_id,
            )
        )
        result = (await self.session.execute(stmt)).scalar_one_or_none()
        if not result:
            raise NotFoundError("Assessment result not found in institution.")

        submission = result.submission
        if not submission or submission.institution_id != institution_id:
            raise NotFoundError("Submission not found for assessment result.")

        # Never generate evidence from unsubmitted or incomplete attempts
        if submission.status not in ["SUBMITTED", "GRADED"]:
            raise ValidationError(
                f"Cannot generate learning evidence from submission in status '{submission.status}'."
            )

        assessment = submission.assessment
        student_user_id = submission.student_user_id
        impacted_skills: Set[uuid.UUID] = set()
        synced_evidences: List[LearningEvidence] = []

        for idx, item in enumerate(result.itemized_breakdown, start=1):
            q_id_str = item.get("question_id")
            if not q_id_str:
                continue

            try:
                question_id = uuid.UUID(q_id_str)
            except ValueError:
                continue

            question = await self.session.get(Question, question_id)
            if not question or question.institution_id != institution_id:
                continue

            # Check if question is mapped to a skill
            target_skill_id = question.skill_id
            target_concept_id = question.concept_id

            if not target_skill_id:
                continue

            awarded = float(item.get("awarded_points", 0.0))
            max_pts = float(item.get("max_points", item.get("allocated_points", 1.0)))
            is_pending = item.get("status") == "PENDING_MANUAL"

            idempotency_key = f"assessment:{result.id}:{question.id}"

            # Check if evidence record already exists for this attempt item
            stmt_ev = select(LearningEvidence).where(
                LearningEvidence.institution_id == institution_id,
                LearningEvidence.idempotency_key == idempotency_key,
            )
            evidence = (await self.session.execute(stmt_ev)).scalar_one_or_none()

            if not evidence:
                evidence = LearningEvidence(
                    id=uuid.uuid4(),
                    institution_id=institution_id,
                    student_user_id=student_user_id,
                    skill_id=target_skill_id,
                    concept_id=target_concept_id,
                    evidence_type="ASSESSMENT_RESULT",
                    title=f"Assessment Question {idx}: {assessment.title}",
                    description=f"Performance on item '{question.prompt_text[:80]}...'",
                    artifact_url=f"/workspace/assessments/{assessment.id}?submission={submission.id}#q_{question.id}",
                    verification_status="PENDING" if is_pending else "VERIFIED",
                    verified_by=result.graded_by if not is_pending else None,
                    verified_at=result.graded_at if not is_pending else None,
                    verification_notes=item.get("feedback", "Automated grading evaluation."),
                    source_assessment_id=assessment.id,
                    source_submission_id=submission.id,
                    source_question_id=question.id,
                    source_result_id=result.id,
                    awarded_score=awarded,
                    max_score=max_pts,
                    rule_version=DeterministicMasteryEngine.RULE_VERSION,
                    idempotency_key=idempotency_key,
                    is_finalized=not is_pending,
                )
                self.session.add(evidence)
            else:
                # Update existing evidence (handles corrections or manual regrading)
                evidence.awarded_score = awarded
                evidence.max_score = max_pts
                evidence.is_finalized = not is_pending
                evidence.verification_status = "PENDING" if is_pending else "VERIFIED"
                evidence.verified_by = result.graded_by if not is_pending else None
                evidence.verified_at = result.graded_at if not is_pending else None
                evidence.verification_notes = item.get("feedback", evidence.verification_notes)

            synced_evidences.append(evidence)
            impacted_skills.add(target_skill_id)

        await self.session.commit()

        # Recalculate student mastery for all impacted skills
        for skill_id in impacted_skills:
            await self.recalculate_student_skill_mastery(
                institution_id=institution_id,
                student_user_id=student_user_id,
                skill_id=skill_id,
            )

        return synced_evidences

    # =========================================================================
    # DETERMINISTIC MASTERY CALCULATION
    # =========================================================================
    async def recalculate_student_skill_mastery(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
        skill_id: uuid.UUID,
    ) -> MasteryRecord:
        """Deterministically calculate student mastery for a skill based on verified evidence."""
        # 1. Fetch verified, finalized evidence for this student and skill
        stmt_ev = select(LearningEvidence).where(
            LearningEvidence.institution_id == institution_id,
            LearningEvidence.student_user_id == student_user_id,
            LearningEvidence.skill_id == skill_id,
            LearningEvidence.verification_status == "VERIFIED",
            LearningEvidence.is_finalized == True,
        )
        ev_items = list((await self.session.execute(stmt_ev)).scalars().all())

        assessment_scores: List[float] = []
        evidence_scores: List[float] = []
        latest_timestamp: Optional[datetime] = None

        for ev in ev_items:
            # Check latest evidence timestamp for decay calculation
            ev_ts = ev.verified_at or ev.created_at
            if ev_ts:
                if latest_timestamp is None or ev_ts > latest_timestamp:
                    latest_timestamp = ev_ts

            if ev.evidence_type == "ASSESSMENT_RESULT" and ev.max_score and ev.max_score > 0:
                score_ratio = min(1.0, max(0.0, (ev.awarded_score or 0.0) / ev.max_score))
                assessment_scores.append(score_ratio)
            else:
                # Verified deliverable, certificate, lab report, code repo
                evidence_scores.append(1.0)

        # 2. Compute raw mastery
        raw_mastery = DeterministicMasteryEngine.calculate_raw_mastery(
            assessment_scores=assessment_scores,
            evidence_scores=evidence_scores,
        )

        # 3. Calculate retention decay
        now = utc_now()
        days_elapsed = 0.0
        if latest_timestamp:
            elapsed_seconds = (now - latest_timestamp).total_seconds()
            days_elapsed = max(0.0, elapsed_seconds / 86400.0)

        decayed_mastery, decay_factor = DeterministicMasteryEngine.calculate_retention_decay(
            raw_mastery=raw_mastery,
            days_elapsed=days_elapsed,
        )

        # 4. Confidence & Competency Classification
        total_obs = len(assessment_scores) + len(evidence_scores)
        confidence = DeterministicMasteryEngine.calculate_confidence(
            assessment_count=len(assessment_scores),
            evidence_count=len(evidence_scores),
        )
        competency_level = DeterministicMasteryEngine.classify_competency(
            mastery_score=decayed_mastery,
            observation_count=total_obs,
        )

        # 5. Provenance audit payload
        provenance = DeterministicMasteryEngine.build_provenance(
            raw_mastery=raw_mastery,
            decay_factor=decay_factor,
            decayed_mastery=decayed_mastery,
            confidence_score=confidence,
            competency_level=competency_level,
            assessment_count=len(assessment_scores),
            evidence_count=len(evidence_scores),
            days_elapsed=days_elapsed,
            calculated_at=now,
        )

        # 6. Upsert MasteryRecord
        stmt_rec = select(MasteryRecord).where(
            MasteryRecord.institution_id == institution_id,
            MasteryRecord.student_user_id == student_user_id,
            MasteryRecord.skill_id == skill_id,
        )
        rec = (await self.session.execute(stmt_rec)).scalar_one_or_none()
        if not rec:
            rec = MasteryRecord(
                id=uuid.uuid4(),
                institution_id=institution_id,
                student_user_id=student_user_id,
                skill_id=skill_id,
                mastery_score=decayed_mastery,
                confidence_score=confidence,
                competency_level=competency_level,
                assessment_count=len(assessment_scores),
                evidence_count=len(evidence_scores),
                decay_factor=decay_factor,
                rule_version=DeterministicMasteryEngine.RULE_VERSION,
                calculation_provenance=provenance,
                is_stale=False,
                last_assessed_at=latest_timestamp or now,
            )
            self.session.add(rec)
        else:
            rec.mastery_score = decayed_mastery
            rec.confidence_score = confidence
            rec.competency_level = competency_level
            rec.assessment_count = len(assessment_scores)
            rec.evidence_count = len(evidence_scores)
            rec.decay_factor = decay_factor
            rec.rule_version = DeterministicMasteryEngine.RULE_VERSION
            rec.calculation_provenance = provenance
            rec.is_stale = False
            rec.last_assessed_at = latest_timestamp or now

        await self.session.commit()
        await self.session.refresh(rec)
        return rec

    async def get_student_mastery_profile(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
    ) -> List[MasteryRecord]:
        stmt = (
            select(MasteryRecord)
            .options(selectinload(MasteryRecord.skill))
            .where(
                MasteryRecord.institution_id == institution_id,
                MasteryRecord.student_user_id == student_user_id,
            )
            .order_by(MasteryRecord.mastery_score.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_student_evidence(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
        skill_id: Optional[uuid.UUID] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[LearningEvidence]:
        stmt = (
            select(LearningEvidence)
            .options(
                selectinload(LearningEvidence.skill),
                selectinload(LearningEvidence.concept),
            )
            .where(
                LearningEvidence.institution_id == institution_id,
                LearningEvidence.student_user_id == student_user_id,
            )
            .order_by(LearningEvidence.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        if skill_id:
            stmt = stmt.where(LearningEvidence.skill_id == skill_id)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # SPACED REPETITION REVIEW SCHEDULING (SM-2)
    # =========================================================================
    async def schedule_concept_review(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
        concept_id: uuid.UUID,
    ) -> ReviewSchedule:
        stmt = select(ReviewSchedule).where(
            ReviewSchedule.institution_id == institution_id,
            ReviewSchedule.student_user_id == student_user_id,
            ReviewSchedule.concept_id == concept_id,
            ReviewSchedule.is_completed == False,
        )
        existing = (await self.session.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

        now = utc_now()
        schedule = ReviewSchedule(
            id=uuid.uuid4(),
            institution_id=institution_id,
            student_user_id=student_user_id,
            concept_id=concept_id,
            interval_days=1,
            repetition_number=0,
            ease_factor=2.5,
            scheduled_for=now,
            is_completed=False,
        )
        self.session.add(schedule)
        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    async def complete_review_session(
        self,
        institution_id: uuid.UUID,
        schedule_id: uuid.UUID,
        student_user_id: uuid.UUID,
        quality_rating: int,
    ) -> ReviewSchedule:
        if quality_rating < 0 or quality_rating > 5:
            raise ValidationError("Review quality rating must be between 0 (blackout) and 5 (perfect).")

        schedule = await self.session.get(ReviewSchedule, schedule_id)
        if not schedule or schedule.institution_id != institution_id:
            raise NotFoundError("Review schedule not found in institution.")

        if schedule.student_user_id != student_user_id:
            raise PermissionDeniedError("Cannot review schedule belonging to another student.")

        next_interval, next_repetition, next_ease = (
            DeterministicMasteryEngine.calculate_sm2_schedule(
                previous_interval_days=schedule.interval_days,
                repetition_number=schedule.repetition_number,
                ease_factor=schedule.ease_factor,
                quality_rating=quality_rating,
            )
        )

        now = utc_now()
        schedule.last_reviewed_at = now
        schedule.interval_days = next_interval
        schedule.repetition_number = next_repetition
        schedule.ease_factor = next_ease
        schedule.scheduled_for = now + (schedule.interval_days * timedelta(days=1))
        schedule.is_completed = quality_rating >= 3

        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule

    async def get_due_reviews_for_student(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
    ) -> List[ReviewSchedule]:
        now = utc_now()
        stmt = (
            select(ReviewSchedule)
            .options(selectinload(ReviewSchedule.concept))
            .where(
                ReviewSchedule.institution_id == institution_id,
                ReviewSchedule.student_user_id == student_user_id,
                ReviewSchedule.scheduled_for <= now,
                ReviewSchedule.is_completed == False,
            )
            .order_by(ReviewSchedule.scheduled_for.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_student_pending_reviews(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
    ) -> List[ReviewSchedule]:
        return await self.get_due_reviews_for_student(institution_id, student_user_id)

    async def complete_concept_review(
        self,
        institution_id: uuid.UUID,
        student_user_id: uuid.UUID,
        schedule_id: uuid.UUID,
        quality_rating: int,
    ) -> ReviewSchedule:
        return await self.complete_review_session(
            institution_id=institution_id,
            schedule_id=schedule_id,
            student_user_id=student_user_id,
            quality_rating=quality_rating,
        )
