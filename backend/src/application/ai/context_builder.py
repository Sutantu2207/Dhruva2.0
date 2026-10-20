"""Dhruva.AI V2 — Provenance-Aware RAG Context Builder.

Enforces:
- Strict tenant boundary isolation: records are bounded by institution_id.
- NO SOURCE -> NO DATA: Context is derived exclusively from verified course syllabi, modules, and concepts.
- Provenance tracking: Every context chunk references its authoritative institutional entity.
"""

import uuid
from typing import Any, Dict, List, NamedTuple, Optional
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.errors import NotFoundError, PermissionDeniedError
from src.domain.academic.models import Course
from src.domain.curriculum.models import Curriculum, Module, Lesson
from src.domain.mastery.models import Concept


class GroundedContext(NamedTuple):
    course_id: uuid.UUID
    course_name: str
    course_code: str
    assembled_context: str
    citations: List[Dict[str, Any]]
    is_out_of_syllabus: bool


class ContextBuilder:
    """Assembles grounded, tenant-isolated context for AI inference."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def build_course_context(
        self,
        institution_id: uuid.UUID,
        course_id: uuid.UUID,
        user_query: str,
    ) -> GroundedContext:
        """Fetches approved syllabus modules and lessons within the institution's scope."""
        # 1. Fetch Course with tenant scoping
        stmt = (
            select(Course)
            .where(
                and_(
                    Course.id == course_id,
                    Course.institution_id == institution_id,
                )
            )
        )
        course = (await self.session.execute(stmt)).scalar_one_or_none()
        if not course:
            # Check if course exists in another tenant (Cross-tenant security check)
            cross_stmt = select(Course).where(Course.id == course_id)
            cross_course = (await self.session.execute(cross_stmt)).scalar_one_or_none()
            if cross_course:
                raise PermissionDeniedError("Cross-tenant course context retrieval is strictly forbidden.")
            raise NotFoundError(f"Course {course_id} not found in this institution.")

        # 2. Fetch Curriculums and Modules for Course
        curr_stmt = (
            select(Curriculum)
            .options(
                selectinload(Curriculum.modules).selectinload(Module.lessons)
            )
            .where(
                and_(
                    Curriculum.course_id == course.id,
                    Curriculum.institution_id == institution_id,
                    Curriculum.status == "PUBLISHED",
                )
            )
        )
        curriculums = list((await self.session.execute(curr_stmt)).scalars().all())

        # 3. Assemble Grounded Modules & Citations
        desc_text = (
            course.course_metadata.get("description", "No official syllabus description.")
            if course.course_metadata
            else "No official syllabus description."
        )
        context_lines: List[str] = [
            f"Institutional Course: {course.title} ({course.code})",
            f"Academic Credits: {course.credits}",
            f"Course Description: {desc_text}",
            "--- Approved Curriculum Modules ---",
        ]
        citations: List[Dict[str, Any]] = []

        total_modules = 0
        all_module_titles: List[str] = []

        for curr in curriculums:
            for mod in curr.modules:
                total_modules += 1
                all_module_titles.append(mod.title.lower())
                context_lines.append(f"Module {mod.sequence_order}: {mod.title}")
                if mod.description:
                    context_lines.append(f"  Summary: {mod.description}")

                citations.append({
                    "citation_id": f"cit-mod-{mod.id}",
                    "source_type": "SYLLABUS_MODULE",
                    "entity_id": str(mod.id),
                    "title": mod.title,
                    "course_code": course.code,
                    "provenance": f"{course.code}/Module-{mod.sequence_order}/{mod.title}",
                })

                for lesson in mod.lessons:
                    context_lines.append(f"  - Lesson {lesson.sequence_order}: {lesson.title}")
                    citations.append({
                        "citation_id": f"cit-les-{lesson.id}",
                        "source_type": "LESSON",
                        "entity_id": str(lesson.id),
                        "title": lesson.title,
                        "course_code": course.code,
                        "provenance": f"{course.code}/Module-{mod.sequence_order}/Lesson-{lesson.sequence_order}",
                    })

        # 4. Out-of-syllabus heuristic detection
        is_out_of_syllabus = False
        query_words = set(user_query.lower().split())
        unrelated_flags = {"cooking", "recipe", "celebrity", "crypto", "astrology", "stock trading"}
        if any(w in query_words for w in unrelated_flags):
            is_out_of_syllabus = True

        assembled_text = "\n".join(context_lines)

        return GroundedContext(
            course_id=course.id,
            course_name=course.title,
            course_code=course.code,
            assembled_context=assembled_text,
            citations=citations,
            is_out_of_syllabus=is_out_of_syllabus,
        )
