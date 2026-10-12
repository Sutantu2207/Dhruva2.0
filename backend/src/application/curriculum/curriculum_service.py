"""Dhruva.AI V2 — Curriculum Application Service.

Encapsulates all domain invariants for curriculum, syllabus, and learning content:
- Versioning and publication lifecycle (DRAFT -> IN_REVIEW -> APPROVED -> PUBLISHED -> ARCHIVED)
- Module and Lesson sequence ordering & validation
- Learning Resource attachments
- Tenant boundary enforcement
- Comprehensive Audit Logging
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.audit.audit_service import AuditService
from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.domain.curriculum.models import (
    Curriculum,
    LearningResource,
    Lesson,
    Module,
)
from src.infrastructure.persistence.postgres.base import utc_now
from src.infrastructure.repositories.academic_repository import AcademicRepository
from src.infrastructure.repositories.curriculum_repository import CurriculumRepository


VALID_STATUS_TRANSITIONS: Dict[str, List[str]] = {
    "DRAFT": ["IN_REVIEW", "ARCHIVED"],
    "IN_REVIEW": ["APPROVED", "DRAFT", "ARCHIVED"],
    "APPROVED": ["PUBLISHED", "DRAFT", "ARCHIVED"],
    "PUBLISHED": ["ARCHIVED"],
    "ARCHIVED": [],
}


class CurriculumService:
    """Service layer enforcing curriculum versioning, syllabus invariants, and content lifecycle."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = CurriculumRepository(session)
        self.academic_repo = AcademicRepository(session)
        self.audit = AuditService(session)

    # =========================================================================
    # CURRICULUMS
    # =========================================================================
    async def create_curriculum(
        self,
        institution_id: uuid.UUID,
        course_id: uuid.UUID,
        title: str,
        program_id: Optional[uuid.UUID] = None,
        academic_year_id: Optional[uuid.UUID] = None,
        description: Optional[str] = None,
        learning_objectives: Optional[List[str]] = None,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> Curriculum:
        course = await self.academic_repo.get_course_by_id(course_id)
        if not course or course.institution_id != institution_id:
            raise NotFoundError("Course", str(course_id))

        if program_id:
            prog = await self.academic_repo.get_program_by_id(program_id)
            if not prog or prog.institution_id != institution_id:
                raise ValidationError("Program not found or does not belong to this institution")

        if academic_year_id:
            ay = await self.academic_repo.get_academic_year_by_id(academic_year_id)
            if not ay or ay.institution_id != institution_id:
                raise ValidationError("Academic year not found or does not belong to this institution")

        clean_title = title.strip()
        if not clean_title:
            raise ValidationError("Curriculum title is required")

        latest_version = await self.repo.get_latest_version_number(course_id)
        new_version = latest_version + 1

        curriculum = Curriculum(
            institution_id=institution_id,
            course_id=course_id,
            program_id=program_id,
            academic_year_id=academic_year_id,
            title=clean_title,
            version=new_version,
            status="DRAFT",
            description=description,
            learning_objectives=learning_objectives or [],
        )
        created = await self.repo.create_curriculum(curriculum)

        await self.audit.log_event(
            action="CURRICULUM_VERSION_CREATED",
            entity_name="Curriculum",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={
                "course_id": str(course_id),
                "title": created.title,
                "version": new_version,
                "status": "DRAFT",
            },
        )
        return created

    async def get_curriculum(self, institution_id: uuid.UUID, curriculum_id: uuid.UUID) -> Curriculum:
        curriculum = await self.repo.get_curriculum_by_id(curriculum_id)
        if not curriculum or curriculum.institution_id != institution_id:
            raise NotFoundError("Curriculum", str(curriculum_id))
        return curriculum

    async def list_curriculums_for_course(
        self, institution_id: uuid.UUID, course_id: uuid.UUID
    ) -> List[Curriculum]:
        course = await self.academic_repo.get_course_by_id(course_id)
        if not course or course.institution_id != institution_id:
            raise NotFoundError("Course", str(course_id))
        return await self.repo.list_curriculums_for_course(course_id)

    async def list_institution_curriculums(
        self, institution_id: uuid.UUID, status: Optional[str] = None
    ) -> List[Curriculum]:
        return await self.repo.list_curriculums_for_institution(institution_id, status=status)

    async def update_curriculum_status(
        self,
        institution_id: uuid.UUID,
        curriculum_id: uuid.UUID,
        target_status: str,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> Curriculum:
        curriculum = await self.get_curriculum(institution_id, curriculum_id)
        current = curriculum.status.upper()
        target = target_status.strip().upper()

        if target not in VALID_STATUS_TRANSITIONS:
            raise ValidationError(f"Invalid curriculum status: '{target_status}'")

        allowed_next = VALID_STATUS_TRANSITIONS.get(current, [])
        if target not in allowed_next:
            raise ValidationError(
                f"Cannot transition curriculum from '{current}' to '{target}'. Allowed: {', '.join(allowed_next) or 'None'}"
            )

        # Integrity check before publication: must have at least one module
        if target == "PUBLISHED":
            modules = await self.repo.list_modules_for_curriculum(curriculum_id)
            if not modules:
                raise ValidationError("Cannot publish curriculum without instructional modules")

        old_status = curriculum.status
        curriculum.status = target

        if target == "APPROVED":
            curriculum.approved_by = actor_user_id
            curriculum.approved_at = utc_now()

        await self.session.flush()

        await self.audit.log_event(
            action="CURRICULUM_STATUS_UPDATED",
            entity_name="Curriculum",
            entity_id=curriculum.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            old_values={"status": old_status},
            new_values={"status": target, "approved_by": str(actor_user_id) if actor_user_id else None},
        )
        return curriculum

    # =========================================================================
    # MODULES
    # =========================================================================
    async def create_module(
        self,
        institution_id: uuid.UUID,
        curriculum_id: uuid.UUID,
        title: str,
        sequence_order: int,
        description: Optional[str] = None,
        estimated_hours: float = 10.0,
        learning_outcomes: Optional[List[str]] = None,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> Module:
        curriculum = await self.get_curriculum(institution_id, curriculum_id)
        if curriculum.status in ("PUBLISHED", "ARCHIVED"):
            raise ValidationError(
                f"Cannot add modules to a {curriculum.status.lower()} curriculum. Create a new version."
            )

        if sequence_order < 1:
            raise ValidationError("sequence_order must be greater than or equal to 1")
        if estimated_hours < 0:
            raise ValidationError("estimated_hours cannot be negative")

        existing = await self.repo.get_module_by_sequence(curriculum_id, sequence_order)
        if existing:
            raise ConflictError(f"Module with sequence order {sequence_order} already exists in this curriculum")

        clean_title = title.strip()
        if not clean_title:
            raise ValidationError("Module title is required")

        module = Module(
            institution_id=institution_id,
            curriculum_id=curriculum_id,
            sequence_order=sequence_order,
            title=clean_title,
            description=description,
            estimated_hours=estimated_hours,
            learning_outcomes=learning_outcomes or [],
        )
        created = await self.repo.create_module(module)

        await self.audit.log_event(
            action="CURRICULUM_MODULE_CREATED",
            entity_name="Module",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={"curriculum_id": str(curriculum_id), "title": clean_title, "seq": sequence_order},
        )
        return created

    async def get_module(self, institution_id: uuid.UUID, module_id: uuid.UUID) -> Module:
        module = await self.repo.get_module_by_id(module_id)
        if not module or module.institution_id != institution_id:
            raise NotFoundError("Module", str(module_id))
        return module

    async def list_modules_for_curriculum(
        self, institution_id: uuid.UUID, curriculum_id: uuid.UUID
    ) -> List[Module]:
        await self.get_curriculum(institution_id, curriculum_id)
        return await self.repo.list_modules_for_curriculum(curriculum_id)

    # =========================================================================
    # LESSONS
    # =========================================================================
    async def create_lesson(
        self,
        institution_id: uuid.UUID,
        module_id: uuid.UUID,
        title: str,
        sequence_order: int,
        content_markdown: Optional[str] = None,
        lesson_type: str = "THEORY",
        duration_minutes: int = 60,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> Lesson:
        module = await self.get_module(institution_id, module_id)
        curriculum = await self.get_curriculum(institution_id, module.curriculum_id)
        if curriculum.status in ("PUBLISHED", "ARCHIVED"):
            raise ValidationError(
                f"Cannot add lessons to a {curriculum.status.lower()} curriculum. Create a new version."
            )

        if sequence_order < 1:
            raise ValidationError("sequence_order must be greater than or equal to 1")
        if duration_minutes <= 0:
            raise ValidationError("duration_minutes must be greater than zero")

        existing = await self.repo.get_lesson_by_sequence(module_id, sequence_order)
        if existing:
            raise ConflictError(f"Lesson with sequence order {sequence_order} already exists in this module")

        clean_title = title.strip()
        if not clean_title:
            raise ValidationError("Lesson title is required")

        lesson = Lesson(
            institution_id=institution_id,
            module_id=module_id,
            sequence_order=sequence_order,
            title=clean_title,
            content_markdown=content_markdown,
            lesson_type=lesson_type.upper(),
            duration_minutes=duration_minutes,
        )
        created = await self.repo.create_lesson(lesson)

        await self.audit.log_event(
            action="CURRICULUM_LESSON_CREATED",
            entity_name="Lesson",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={"module_id": str(module_id), "title": clean_title, "seq": sequence_order},
        )
        return created

    async def get_lesson(self, institution_id: uuid.UUID, lesson_id: uuid.UUID) -> Lesson:
        lesson = await self.repo.get_lesson_by_id(lesson_id)
        if not lesson or lesson.institution_id != institution_id:
            raise NotFoundError("Lesson", str(lesson_id))
        return lesson

    async def list_lessons_for_module(self, institution_id: uuid.UUID, module_id: uuid.UUID) -> List[Lesson]:
        await self.get_module(institution_id, module_id)
        return await self.repo.list_lessons_for_module(module_id)

    # =========================================================================
    # LEARNING RESOURCES
    # =========================================================================
    async def create_learning_resource(
        self,
        institution_id: uuid.UUID,
        lesson_id: uuid.UUID,
        title: str,
        resource_type: str = "DOCUMENT",
        storage_uri: Optional[str] = None,
        external_url: Optional[str] = None,
        resource_metadata: Optional[Dict[str, Any]] = None,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> LearningResource:
        lesson = await self.get_lesson(institution_id, lesson_id)
        module = await self.get_module(institution_id, lesson.module_id)
        curriculum = await self.get_curriculum(institution_id, module.curriculum_id)
        if curriculum.status in ("PUBLISHED", "ARCHIVED"):
            raise ValidationError(
                f"Cannot attach resources to a {curriculum.status.lower()} curriculum. Create a new version."
            )

        clean_title = title.strip()
        if not clean_title:
            raise ValidationError("Learning resource title is required")

        resource = LearningResource(
            institution_id=institution_id,
            lesson_id=lesson_id,
            title=clean_title,
            resource_type=resource_type.upper(),
            storage_uri=storage_uri,
            external_url=external_url,
            resource_metadata=resource_metadata or {},
        )
        created = await self.repo.create_learning_resource(resource)

        await self.audit.log_event(
            action="CURRICULUM_RESOURCE_ATTACHED",
            entity_name="LearningResource",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={"lesson_id": str(lesson_id), "title": clean_title, "type": resource_type},
        )
        return created

    async def list_resources_for_lesson(
        self, institution_id: uuid.UUID, lesson_id: uuid.UUID
    ) -> List[LearningResource]:
        await self.get_lesson(institution_id, lesson_id)
        return await self.repo.list_resources_for_lesson(lesson_id)
