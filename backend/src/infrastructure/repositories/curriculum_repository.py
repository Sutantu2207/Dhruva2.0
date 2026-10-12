"""Dhruva.AI V2 — Curriculum & Learning Content Repository.

Persistence layer for versioned curriculums, modules, lessons, and educational resources.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.curriculum.models import (
    Curriculum,
    LearningResource,
    Lesson,
    Module,
)


class CurriculumRepository:
    """Async repository governing curriculum and syllabus structures with strict institution scoping."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---------------- Curriculum Operations ----------------
    async def create_curriculum(self, curriculum: Curriculum) -> Curriculum:
        self.session.add(curriculum)
        await self.session.flush()
        return curriculum

    async def get_curriculum_by_id(self, curriculum_id: uuid.UUID) -> Optional[Curriculum]:
        stmt = select(Curriculum).where(Curriculum.id == curriculum_id, Curriculum.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_curriculum_by_course_and_version(
        self, course_id: uuid.UUID, version: int
    ) -> Optional[Curriculum]:
        stmt = select(Curriculum).where(
            Curriculum.course_id == course_id,
            Curriculum.version == version,
            Curriculum.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_curriculums_for_course(self, course_id: uuid.UUID) -> List[Curriculum]:
        stmt = select(Curriculum).where(
            Curriculum.course_id == course_id,
            Curriculum.deleted_at.is_(None),
        ).order_by(desc(Curriculum.version))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_version_number(self, course_id: uuid.UUID) -> int:
        stmt = select(func.max(Curriculum.version)).where(
            Curriculum.course_id == course_id,
            Curriculum.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        max_ver = result.scalar_one_or_none()
        return max_ver if max_ver is not None else 0

    async def list_curriculums_for_institution(
        self, institution_id: uuid.UUID, status: Optional[str] = None
    ) -> List[Curriculum]:
        conditions = [Curriculum.institution_id == institution_id, Curriculum.deleted_at.is_(None)]
        if status:
            conditions.append(Curriculum.status == status.upper())
        stmt = select(Curriculum).where(and_(*conditions)).order_by(Curriculum.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ---------------- Module Operations ----------------
    async def create_module(self, module: Module) -> Module:
        self.session.add(module)
        await self.session.flush()
        return module

    async def get_module_by_id(self, module_id: uuid.UUID) -> Optional[Module]:
        stmt = select(Module).where(Module.id == module_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_modules_for_curriculum(self, curriculum_id: uuid.UUID) -> List[Module]:
        stmt = select(Module).where(Module.curriculum_id == curriculum_id).order_by(Module.sequence_order.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_module_by_sequence(self, curriculum_id: uuid.UUID, sequence_order: int) -> Optional[Module]:
        stmt = select(Module).where(
            Module.curriculum_id == curriculum_id,
            Module.sequence_order == sequence_order,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ---------------- Lesson Operations ----------------
    async def create_lesson(self, lesson: Lesson) -> Lesson:
        self.session.add(lesson)
        await self.session.flush()
        return lesson

    async def get_lesson_by_id(self, lesson_id: uuid.UUID) -> Optional[Lesson]:
        stmt = select(Lesson).where(Lesson.id == lesson_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_lessons_for_module(self, module_id: uuid.UUID) -> List[Lesson]:
        stmt = select(Lesson).where(Lesson.module_id == module_id).order_by(Lesson.sequence_order.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_lesson_by_sequence(self, module_id: uuid.UUID, sequence_order: int) -> Optional[Lesson]:
        stmt = select(Lesson).where(
            Lesson.module_id == module_id,
            Lesson.sequence_order == sequence_order,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ---------------- Learning Resource Operations ----------------
    async def create_learning_resource(self, resource: LearningResource) -> LearningResource:
        self.session.add(resource)
        await self.session.flush()
        return resource

    async def get_learning_resource_by_id(self, resource_id: uuid.UUID) -> Optional[LearningResource]:
        stmt = select(LearningResource).where(LearningResource.id == resource_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_resources_for_lesson(self, lesson_id: uuid.UUID) -> List[LearningResource]:
        stmt = select(LearningResource).where(LearningResource.lesson_id == lesson_id).order_by(LearningResource.created_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
