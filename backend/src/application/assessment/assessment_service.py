"""Dhruva.AI V2 — Assessment & Grading Application Service.

Coordinates:
- Question Bank Authoring with strict server-side validation.
- Assessment scheduling, mark allocation, and publication state machine.
- Secure Student Submissions with enrollment verification, attempt caps, and server timestamp gates.
- Invocation of DeterministicGradingEngine with zero LLM-hallucinated grades.
- Manual evaluation review workflows and immutable audit trails.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.assessment.grading_engine import DeterministicGradingEngine
from src.application.audit.audit_service import AuditService
from src.core.errors import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from src.domain.academic.models import CourseOffering, StudentEnrollment
from src.domain.assessment.models import (
    Assessment,
    AssessmentQuestion,
    AssessmentResult,
    AssessmentSubmission,
    Question,
    QuestionBank,
)
from src.domain.identity.models import User
from src.infrastructure.persistence.postgres.base import utc_now
from src.infrastructure.repositories.assessment_repository import AssessmentRepository


class AssessmentService:
    """Application Service orchestrating the assessment lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AssessmentRepository(session)
        self.audit = AuditService(session)

    # =========================================================================
    # 1. QUESTION BANKS
    # =========================================================================
    async def create_question_bank(
        self,
        institution_id: uuid.UUID,
        title: str,
        creator_user: User,
        description: str = "",
        course_id: Optional[uuid.UUID] = None,
        department_id: Optional[uuid.UUID] = None,
    ) -> QuestionBank:
        clean_title = title.strip()
        if not clean_title:
            raise ValidationError("Question bank title cannot be empty.")

        bank = QuestionBank(
            institution_id=institution_id,
            title=clean_title,
            description=description.strip(),
            course_id=course_id,
            department_id=department_id,
            created_by=creator_user.id,
        )
        saved = await self.repo.create_question_bank(bank)

        await self.audit.log_event(
            action="QUESTION_BANK_CREATED",
            entity_name="QuestionBank",
            entity_id=saved.id,
            institution_id=institution_id,
            actor_user_id=creator_user.id,
            new_values={"title": saved.title, "course_id": str(course_id) if course_id else None},
        )
        return saved

    async def get_question_bank(
        self, institution_id: uuid.UUID, bank_id: uuid.UUID
    ) -> QuestionBank:
        bank = await self.repo.get_question_bank_by_id(institution_id, bank_id)
        if not bank:
            raise NotFoundError(f"Question bank {bank_id} not found.")
        return bank

    async def list_question_banks(
        self,
        institution_id: uuid.UUID,
        course_id: Optional[uuid.UUID] = None,
        department_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[QuestionBank]:
        return await self.repo.list_question_banks(
            institution_id=institution_id,
            course_id=course_id,
            department_id=department_id,
            limit=limit,
            offset=offset,
        )

    # =========================================================================
    # 2. QUESTIONS (AUTHORING & SERVER-SIDE VALIDATION)
    # =========================================================================
    async def create_question(
        self,
        institution_id: uuid.UUID,
        question_bank_id: uuid.UUID,
        question_type: str,
        prompt_text: str,
        answer_key: Dict[str, Any],
        creator_user: User,
        options: Optional[List[Dict[str, Any]]] = None,
        points: float = 1.0,
        difficulty: str = "MEDIUM",
        explanation: str = "",
        concept_id: Optional[uuid.UUID] = None,
        skill_id: Optional[uuid.UUID] = None,
    ) -> Question:
        # 1. Verify question bank exists in this tenant
        bank = await self.get_question_bank(institution_id, question_bank_id)

        # 2. Validate question attributes
        clean_prompt = prompt_text.strip()
        if not clean_prompt:
            raise ValidationError("Question prompt text cannot be empty.")

        if points <= 0:
            raise ValidationError("Question points must be strictly greater than 0.")

        qtype = question_type.upper().strip()
        if qtype not in ("MCQ", "MULTI_SELECT", "NUMERICAL", "STRUCTURED_TEXT"):
            raise ValidationError(
                f"Unsupported question type '{question_type}'. Must be one of: MCQ, MULTI_SELECT, NUMERICAL, STRUCTURED_TEXT."
            )

        clean_options = options or []

        # 3. Server-side validation per question type
        if qtype == "MCQ":
            if len(clean_options) < 2:
                raise ValidationError("MCQ questions must provide at least 2 options.")
            option_ids = {str(opt.get("id", "")).strip() for opt in clean_options if opt.get("id")}
            if len(option_ids) != len(clean_options):
                raise ValidationError("All option IDs must be unique and non-empty.")

            correct_id = str(answer_key.get("correct_option_id", "")).strip()
            if not correct_id or correct_id not in option_ids:
                raise ValidationError(
                    f"MCQ answer key 'correct_option_id' ('{correct_id}') must match one of the valid options: {sorted(option_ids)}."
                )

        elif qtype == "MULTI_SELECT":
            if len(clean_options) < 2:
                raise ValidationError("Multi-select questions must provide at least 2 options.")
            option_ids = {str(opt.get("id", "")).strip() for opt in clean_options if opt.get("id")}
            if len(option_ids) != len(clean_options):
                raise ValidationError("All option IDs must be unique and non-empty.")

            correct_ids = [str(cid).strip() for cid in answer_key.get("correct_option_ids", []) if str(cid).strip()]
            if not correct_ids:
                raise ValidationError("Multi-select answer key must specify at least one correct_option_id.")
            for cid in correct_ids:
                if cid not in option_ids:
                    raise ValidationError(
                        f"Correct option ID '{cid}' does not match any valid options in {sorted(option_ids)}."
                    )

        elif qtype == "NUMERICAL":
            if "target_value" not in answer_key:
                raise ValidationError("Numerical answer key must specify 'target_value'.")
            try:
                float(answer_key["target_value"])
            except (ValueError, TypeError):
                raise ValidationError("Numerical 'target_value' must be a valid float.")

            if "tolerance" in answer_key:
                try:
                    tol = float(answer_key["tolerance"])
                    if tol < 0:
                        raise ValidationError("Numerical 'tolerance' cannot be negative.")
                except (ValueError, TypeError):
                    raise ValidationError("Numerical 'tolerance' must be a valid non-negative float.")

        elif qtype == "STRUCTURED_TEXT":
            if not answer_key.get("rubric"):
                raise ValidationError("Structured text questions must specify evaluation rubric in answer key.")

        question = Question(
            institution_id=institution_id,
            question_bank_id=bank.id,
            question_type=qtype,
            prompt_text=clean_prompt,
            options=clean_options,
            answer_key=answer_key,
            points=round(points, 4),
            difficulty=difficulty.upper().strip(),
            explanation=explanation.strip(),
            concept_id=concept_id,
            skill_id=skill_id,
        )
        saved = await self.repo.create_question(question)

        await self.audit.log_event(
            action="QUESTION_CREATED",
            entity_name="Question",
            entity_id=saved.id,
            institution_id=institution_id,
            actor_user_id=creator_user.id,
            new_values={"question_type": qtype, "points": saved.points, "bank_id": str(bank.id)},
        )
        return saved

    async def get_question(
        self, institution_id: uuid.UUID, question_id: uuid.UUID
    ) -> Question:
        question = await self.repo.get_question_by_id(institution_id, question_id)
        if not question:
            raise NotFoundError(f"Question {question_id} not found.")
        return question

    async def list_questions_by_bank(
        self,
        institution_id: uuid.UUID,
        question_bank_id: uuid.UUID,
        question_type: Optional[str] = None,
    ) -> List[Question]:
        await self.get_question_bank(institution_id, question_bank_id)
        return await self.repo.list_questions_by_bank(
            institution_id=institution_id,
            question_bank_id=question_bank_id,
            question_type=question_type,
        )

    # =========================================================================
    # 3. ASSESSMENTS
    # =========================================================================
    async def create_assessment(
        self,
        institution_id: uuid.UUID,
        course_offering_id: uuid.UUID,
        title: str,
        publish_at: datetime,
        due_at: datetime,
        creator_user: User,
        instructions: str = "",
        assessment_type: str = "QUIZ",
        duration_minutes: Optional[int] = None,
        passing_percentage: float = 40.0,
        max_attempts: int = 1,
    ) -> Assessment:
        clean_title = title.strip()
        if not clean_title:
            raise ValidationError("Assessment title cannot be empty.")

        # Validate offering exists in institution
        stmt = select(CourseOffering).where(
            CourseOffering.id == course_offering_id,
            CourseOffering.institution_id == institution_id,
        )
        res = await self.session.execute(stmt)
        offering = res.scalar_one_or_none()
        if not offering:
            raise NotFoundError(f"Course offering {course_offering_id} not found in this institution.")

        # Ensure timezone-aware UTC timestamps
        if publish_at >= due_at:
            raise ValidationError("Assessment 'publish_at' must be strictly before 'due_at'.")

        if not (0.0 <= passing_percentage <= 100.0):
            raise ValidationError("Passing percentage must be between 0.0 and 100.0.")

        if max_attempts < 1:
            raise ValidationError("Max attempts must be at least 1.")

        assessment = Assessment(
            institution_id=institution_id,
            course_offering_id=course_offering_id,
            title=clean_title,
            instructions=instructions.strip(),
            assessment_type=assessment_type.upper().strip(),
            status="DRAFT",
            publish_at=publish_at,
            due_at=due_at,
            duration_minutes=duration_minutes,
            total_points=0.0,
            passing_percentage=round(passing_percentage, 2),
            max_attempts=max_attempts,
            created_by=creator_user.id,
        )
        saved = await self.repo.create_assessment(assessment)

        await self.audit.log_event(
            action="ASSESSMENT_CREATED",
            entity_name="Assessment",
            entity_id=saved.id,
            institution_id=institution_id,
            actor_user_id=creator_user.id,
            new_values={"title": saved.title, "offering_id": str(course_offering_id)},
        )
        return saved

    async def get_assessment(
        self, institution_id: uuid.UUID, assessment_id: uuid.UUID
    ) -> Assessment:
        assessment = await self.repo.get_assessment_by_id(institution_id, assessment_id)
        if not assessment:
            raise NotFoundError(f"Assessment {assessment_id} not found.")
        return assessment

    async def list_assessments(
        self,
        institution_id: uuid.UUID,
        course_offering_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Assessment]:
        return await self.repo.list_assessments(
            institution_id=institution_id,
            course_offering_id=course_offering_id,
            status=status,
            limit=limit,
            offset=offset,
        )

    async def add_question_to_assessment(
        self,
        institution_id: uuid.UUID,
        assessment_id: uuid.UUID,
        question_id: uuid.UUID,
        points: Optional[float] = None,
        sort_order: Optional[int] = None,
    ) -> AssessmentQuestion:
        assessment = await self.get_assessment(institution_id, assessment_id)
        if assessment.status != "DRAFT":
            raise ConflictError(f"Cannot modify questions in assessment with status '{assessment.status}'. Questions are locked once published.")

        question = await self.get_question(institution_id, question_id)

        # Check if already added
        existing = [q for q in assessment.questions if q.question_id == question_id]
        if existing:
            raise ConflictError("Question has already been added to this assessment.")

        allocated_points = points if points is not None else question.points
        if allocated_points <= 0:
            raise ValidationError("Allocated points for question must be strictly positive.")

        next_order = sort_order if sort_order is not None else len(assessment.questions)

        link = AssessmentQuestion(
            id=uuid.uuid4(),
            assessment_id=assessment.id,
            question_id=question.id,
            points=round(allocated_points, 4),
            sort_order=next_order,
        )
        saved_link = await self.repo.add_question_to_assessment(link)

        # Recalculate total_points
        assessment.total_points = round(
            sum(q.points for q in assessment.questions) + saved_link.points, 4
        )
        await self.session.flush()

        return saved_link

    async def publish_assessment(
        self,
        institution_id: uuid.UUID,
        assessment_id: uuid.UUID,
        publisher_user: User,
    ) -> Assessment:
        assessment = await self.get_assessment(institution_id, assessment_id)
        if assessment.status == "PUBLISHED":
            return assessment

        if assessment.status in ("CLOSED", "ARCHIVED"):
            raise ConflictError(f"Cannot publish assessment currently in '{assessment.status}' status.")

        if len(assessment.questions) == 0:
            raise ConflictError("Cannot publish an assessment with zero questions.")

        if assessment.total_points <= 0:
            raise ValidationError("Assessment total points must be greater than zero before publishing.")

        assessment.status = "PUBLISHED"
        await self.session.flush()

        await self.audit.log_event(
            action="ASSESSMENT_PUBLISHED",
            entity_name="Assessment",
            entity_id=assessment.id,
            institution_id=institution_id,
            actor_user_id=publisher_user.id,
            new_values={
                "title": assessment.title,
                "total_points": assessment.total_points,
                "questions_count": len(assessment.questions),
            },
        )
        return await self.get_assessment(institution_id, assessment_id)

    # =========================================================================
    # 4. SUBMISSIONS & STUDENT ATTEMPTS
    # =========================================================================
    async def submit_assessment(
        self,
        institution_id: uuid.UUID,
        assessment_id: uuid.UUID,
        student_user: User,
        answers_payload: Dict[str, Any],
    ) -> AssessmentSubmission:
        """
        Record a student's finalized submission attempt and trigger deterministic autograding.
        Enforces enrollment, schedule windows, and attempt caps.
        """
        assessment = await self.get_assessment(institution_id, assessment_id)

        # 1. Verify assessment publication status
        if assessment.status != "PUBLISHED":
            raise ConflictError(
                f"Assessment '{assessment.title}' is not open for submissions (current status: {assessment.status})."
            )

        # 2. Check active schedule window (using authoritative server time)
        def to_utc(dt: datetime) -> datetime:
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)

        current_time = to_utc(utc_now())
        publish_at_utc = to_utc(assessment.publish_at)
        due_at_utc = to_utc(assessment.due_at)

        if current_time < publish_at_utc:
            raise ConflictError("Assessment submission window has not opened yet.")

        if current_time > due_at_utc:
            raise ConflictError("Assessment submission deadline has passed.")

        # 3. Verify student enrollment in course offering
        enrollment_stmt = select(StudentEnrollment).where(
            StudentEnrollment.institution_id == institution_id,
            StudentEnrollment.course_offering_id == assessment.course_offering_id,
            StudentEnrollment.student_user_id == student_user.id,
            StudentEnrollment.enrollment_status == "ENROLLED",
        )
        enrollment_res = await self.session.execute(enrollment_stmt)
        enrollment = enrollment_res.scalar_one_or_none()
        if not enrollment:
            raise PermissionDeniedError(
                "You are not actively enrolled in the course offering associated with this assessment."
            )

        # 4. Check attempt limits
        attempt_count = await self.repo.count_student_attempts(assessment.id, student_user.id)
        if attempt_count >= assessment.max_attempts:
            raise ConflictError(
                f"You have reached the maximum allowed attempts ({assessment.max_attempts}) for this assessment."
            )

        next_attempt = attempt_count + 1

        # 5. Persist submission
        submission = AssessmentSubmission(
            id=uuid.uuid4(),
            institution_id=institution_id,
            assessment_id=assessment.id,
            student_user_id=student_user.id,
            attempt_number=next_attempt,
            answers_payload=answers_payload,
            status="SUBMITTED",
            started_at=current_time,
            submitted_at=current_time,
        )
        saved_submission = await self.repo.create_submission(submission)

        # 6. Execute Deterministic Autograder
        q_dicts = [
            {
                "id": str(aq.question.id),
                "question_type": aq.question.question_type,
                "points": aq.points,
                "answer_key": aq.question.answer_key,
                "prompt_text": aq.question.prompt_text,
            }
            for aq in assessment.questions
        ]

        grade_output = DeterministicGradingEngine.grade_submission(
            assessment_questions=q_dicts,
            answers_payload=answers_payload,
            passing_percentage=assessment.passing_percentage,
        )

        # 7. Persist Result
        result_record = AssessmentResult(
            id=uuid.uuid4(),
            institution_id=institution_id,
            submission_id=saved_submission.id,
            raw_score=grade_output["raw_score"],
            total_points=grade_output["total_points"],
            percentage=grade_output["percentage"],
            grade_letter=grade_output["grade_letter"],
            is_passed=grade_output["is_passed"],
            itemized_breakdown=grade_output["itemized_breakdown"],
            is_finalized=grade_output["is_finalized"],
            graded_by=None,  # Auto-graded deterministically
            graded_at=current_time,
        )
        await self.repo.create_result(result_record)

        if grade_output["is_finalized"]:
            saved_submission.status = "GRADED"
        else:
            saved_submission.status = "PENDING_REVIEW"

        saved_submission.result = result_record
        await self.session.flush()

        await self.audit.log_event(
            action="ASSESSMENT_SUBMISSION_EVALUATED",
            entity_name="AssessmentSubmission",
            entity_id=saved_submission.id,
            institution_id=institution_id,
            actor_user_id=student_user.id,
            new_values={
                "attempt_number": next_attempt,
                "score": grade_output["raw_score"],
                "percentage": grade_output["percentage"],
                "is_finalized": grade_output["is_finalized"],
            },
        )

        loaded_sub = await self.repo.get_submission_by_id(institution_id, saved_submission.id)
        return loaded_sub or saved_submission

    async def get_submission(
        self,
        institution_id: uuid.UUID,
        submission_id: uuid.UUID,
        requesting_user: User,
    ) -> AssessmentSubmission:
        submission = await self.repo.get_submission_by_id(institution_id, submission_id)
        if not submission:
            raise NotFoundError(f"Submission {submission_id} not found.")

        # Access check: students can only view their own submission
        is_owner = submission.student_user_id == requesting_user.id
        is_faculty_or_admin = any(
            r in ("SUPER_ADMIN", "INSTITUTION_ADMIN", "HOD", "FACULTY")
            for r in requesting_user.roles
        )
        if not is_owner and not is_faculty_or_admin:
            raise PermissionDeniedError("You do not have permission to view another student's submission.")

        return submission

    # =========================================================================
    # 5. MANUAL GRADING WORKFLOW (SUBJECTIVE / STRUCTURED TEXT)
    # =========================================================================
    async def grade_manual_question(
        self,
        institution_id: uuid.UUID,
        submission_id: uuid.UUID,
        question_id: uuid.UUID,
        awarded_points: float,
        reviewer_user: User,
        feedback: str = "",
    ) -> AssessmentResult:
        """
        Record authorized manual evaluation for a subjective question.
        Re-evaluates aggregate scores deterministically.
        """
        submission = await self.repo.get_submission_by_id(institution_id, submission_id)
        if not submission:
            raise NotFoundError(f"Submission {submission_id} not found.")

        result = await self.repo.get_result_by_submission_id(institution_id, submission_id)
        if not result:
            raise NotFoundError(f"No result record found for submission {submission_id}.")

        assessment = submission.assessment

        # Find target question in assessment
        target_aq = next(
            (aq for aq in assessment.questions if aq.question_id == question_id), None
        )
        if not target_aq:
            raise NotFoundError(f"Question {question_id} is not part of assessment {assessment.id}.")

        if awarded_points < 0 or awarded_points > target_aq.points:
            raise ValidationError(
                f"Awarded points must be between 0.0 and maximum configured points ({target_aq.points})."
            )

        # Update itemized item
        updated_itemized = list(result.itemized_breakdown)
        found = False
        has_pending = False

        for item in updated_itemized:
            if str(item.get("question_id")) == str(question_id):
                item["awarded_points"] = round(awarded_points, 4)
                item["status"] = "MANUALLY_GRADED"
                item["feedback"] = feedback.strip() or "Evaluated by course faculty."
                found = True
            elif item.get("status") == "PENDING_MANUAL":
                has_pending = True

        if not found:
            updated_itemized.append({
                "question_id": str(question_id),
                "question_type": target_aq.question.question_type,
                "max_points": target_aq.points,
                "awarded_points": round(awarded_points, 4),
                "status": "MANUALLY_GRADED",
                "feedback": feedback.strip() or "Evaluated by course faculty.",
            })

        # Recalculate totals
        raw_score = sum(float(item.get("awarded_points", 0.0)) for item in updated_itemized)
        total_possible = sum(float(item.get("max_points", 0.0)) for item in updated_itemized)
        raw_score = min(raw_score, total_possible)

        if total_possible > 0:
            percentage = round((raw_score / total_possible) * 100.0, 2)
        else:
            percentage = 0.0

        result.raw_score = round(raw_score, 4)
        result.total_points = round(total_possible, 4)
        result.percentage = percentage
        result.grade_letter = DeterministicGradingEngine.calculate_grade_letter(percentage)
        result.is_passed = percentage >= assessment.passing_percentage
        result.itemized_breakdown = updated_itemized
        result.is_finalized = not has_pending
        result.graded_by = reviewer_user.id
        result.graded_at = utc_now()

        if result.is_finalized:
            submission.status = "GRADED"

        await self.session.flush()

        await self.audit.log_event(
            action="MANUAL_GRADE_EVALUATED",
            entity_name="AssessmentResult",
            entity_id=result.id,
            institution_id=institution_id,
            actor_user_id=reviewer_user.id,
            new_values={
                "question_id": str(question_id),
                "awarded_points": awarded_points,
                "new_total": result.raw_score,
                "is_finalized": result.is_finalized,
            },
        )

        return result
