"""Dhruva.AI V2 — Assessment, Question Bank & Grading Persistence Repository.

Provides transactional persistence and query methods for:
- Question Banks & Question entities
- Assessment configuration and question links
- Student Submissions and Attempts
- Deterministic Results and Itemized Evaluations
"""

import uuid
from typing import List, Optional
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.assessment.models import (
    Assessment,
    AssessmentQuestion,
    AssessmentResult,
    AssessmentSubmission,
    Question,
    QuestionBank,
)


class AssessmentRepository:
    """Async SQLAlchemy persistence repository for the assessment domain."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # =========================================================================
    # QUESTION BANKS
    # =========================================================================
    async def create_question_bank(self, bank: QuestionBank) -> QuestionBank:
        self.session.add(bank)
        await self.session.flush()
        return bank

    async def get_question_bank_by_id(
        self, institution_id: uuid.UUID, bank_id: uuid.UUID
    ) -> Optional[QuestionBank]:
        stmt = (
            select(QuestionBank)
            .where(
                QuestionBank.id == bank_id,
                QuestionBank.institution_id == institution_id,
            )
            .options(selectinload(QuestionBank.questions))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_question_banks(
        self,
        institution_id: uuid.UUID,
        course_id: Optional[uuid.UUID] = None,
        department_id: Optional[uuid.UUID] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[QuestionBank]:
        stmt = (
            select(QuestionBank)
            .where(QuestionBank.institution_id == institution_id)
            .order_by(QuestionBank.created_at.desc())
        )
        if course_id:
            stmt = stmt.where(QuestionBank.course_id == course_id)
        if department_id:
            stmt = stmt.where(QuestionBank.department_id == department_id)

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # QUESTIONS
    # =========================================================================
    async def create_question(self, question: Question) -> Question:
        self.session.add(question)
        await self.session.flush()
        return question

    async def get_question_by_id(
        self, institution_id: uuid.UUID, question_id: uuid.UUID
    ) -> Optional[Question]:
        stmt = select(Question).where(
            Question.id == question_id,
            Question.institution_id == institution_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_questions_by_bank(
        self,
        institution_id: uuid.UUID,
        question_bank_id: uuid.UUID,
        question_type: Optional[str] = None,
    ) -> List[Question]:
        stmt = (
            select(Question)
            .where(
                Question.institution_id == institution_id,
                Question.question_bank_id == question_bank_id,
            )
            .order_by(Question.created_at.asc())
        )
        if question_type:
            stmt = stmt.where(Question.question_type == question_type)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_question(self, question: Question) -> None:
        await self.session.delete(question)
        await self.session.flush()

    # =========================================================================
    # ASSESSMENTS
    # =========================================================================
    async def create_assessment(self, assessment: Assessment) -> Assessment:
        self.session.add(assessment)
        await self.session.flush()
        loaded = await self.get_assessment_by_id(assessment.institution_id, assessment.id)
        return loaded or assessment

    async def get_assessment_by_id(
        self, institution_id: uuid.UUID, assessment_id: uuid.UUID
    ) -> Optional[Assessment]:
        stmt = (
            select(Assessment)
            .where(
                Assessment.id == assessment_id,
                Assessment.institution_id == institution_id,
            )
            .options(
                selectinload(Assessment.questions).selectinload(AssessmentQuestion.question)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_assessments(
        self,
        institution_id: uuid.UUID,
        course_offering_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Assessment]:
        stmt = (
            select(Assessment)
            .where(Assessment.institution_id == institution_id)
            .options(
                selectinload(Assessment.questions).selectinload(AssessmentQuestion.question)
            )
            .order_by(Assessment.publish_at.desc())
        )
        if course_offering_id:
            stmt = stmt.where(Assessment.course_offering_id == course_offering_id)
        if status:
            stmt = stmt.where(Assessment.status == status)

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_assessments(
        self,
        institution_id: uuid.UUID,
        course_offering_id: Optional[uuid.UUID] = None,
        status: Optional[str] = None,
    ) -> int:
        stmt = (
            select(func.count(Assessment.id))
            .where(Assessment.institution_id == institution_id)
        )
        if course_offering_id:
            stmt = stmt.where(Assessment.course_offering_id == course_offering_id)
        if status:
            stmt = stmt.where(Assessment.status == status)

        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def add_question_to_assessment(
        self, link: AssessmentQuestion
    ) -> AssessmentQuestion:
        self.session.add(link)
        await self.session.flush()
        return link

    async def remove_question_from_assessment(
        self, assessment_id: uuid.UUID, question_id: uuid.UUID
    ) -> None:
        stmt = delete(AssessmentQuestion).where(
            AssessmentQuestion.assessment_id == assessment_id,
            AssessmentQuestion.question_id == question_id,
        )
        await self.session.execute(stmt)
        await self.session.flush()

    # =========================================================================
    # SUBMISSIONS & ATTEMPTS
    # =========================================================================
    async def create_submission(
        self, submission: AssessmentSubmission
    ) -> AssessmentSubmission:
        self.session.add(submission)
        await self.session.flush()
        return submission

    async def get_submission_by_id(
        self, institution_id: uuid.UUID, submission_id: uuid.UUID
    ) -> Optional[AssessmentSubmission]:
        stmt = (
            select(AssessmentSubmission)
            .where(
                AssessmentSubmission.id == submission_id,
                AssessmentSubmission.institution_id == institution_id,
            )
            .options(
                selectinload(AssessmentSubmission.result),
                selectinload(AssessmentSubmission.assessment).selectinload(Assessment.questions).selectinload(AssessmentQuestion.question),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_submission_by_attempt(
        self,
        assessment_id: uuid.UUID,
        student_user_id: uuid.UUID,
        attempt_number: int,
    ) -> Optional[AssessmentSubmission]:
        stmt = select(AssessmentSubmission).where(
            AssessmentSubmission.assessment_id == assessment_id,
            AssessmentSubmission.student_user_id == student_user_id,
            AssessmentSubmission.attempt_number == attempt_number,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def count_student_attempts(
        self, assessment_id: uuid.UUID, student_user_id: uuid.UUID
    ) -> int:
        stmt = select(func.count(AssessmentSubmission.id)).where(
            AssessmentSubmission.assessment_id == assessment_id,
            AssessmentSubmission.student_user_id == student_user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar() or 0

    async def list_submissions_for_assessment(
        self,
        institution_id: uuid.UUID,
        assessment_id: uuid.UUID,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AssessmentSubmission]:
        stmt = (
            select(AssessmentSubmission)
            .where(
                AssessmentSubmission.institution_id == institution_id,
                AssessmentSubmission.assessment_id == assessment_id,
            )
            .order_by(AssessmentSubmission.started_at.desc())
            .options(selectinload(AssessmentSubmission.result))
        )
        if status:
            stmt = stmt.where(AssessmentSubmission.status == status)

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # =========================================================================
    # RESULTS
    # =========================================================================
    async def create_result(self, result: AssessmentResult) -> AssessmentResult:
        self.session.add(result)
        await self.session.flush()
        return result

    async def get_result_by_submission_id(
        self, institution_id: uuid.UUID, submission_id: uuid.UUID
    ) -> Optional[AssessmentResult]:
        stmt = select(AssessmentResult).where(
            AssessmentResult.submission_id == submission_id,
            AssessmentResult.institution_id == institution_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
