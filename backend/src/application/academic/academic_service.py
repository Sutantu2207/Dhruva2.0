"""Dhruva.AI V2 — Academic Application Service.

Encapsulates all domain and business rules for institutional hierarchy:
- Departments, Programs, Batches, Sections
- Academic Years and Semesters (date & relationship validation)
- Course Catalog & Course Offerings
- Faculty Teaching Assignments & Student Enrollments (with duplicate & capacity guards)
- Comprehensive Audit Logging
"""

import uuid
from datetime import date
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.audit.audit_service import AuditService
from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.domain.academic.models import (
    AcademicYear,
    Batch,
    Course,
    CourseOffering,
    Department,
    FacultyProfile,
    Program,
    Section,
    Semester,
    StudentEnrollment,
    StudentProfile,
    TeachingAssignment,
)
from src.infrastructure.repositories.academic_repository import AcademicRepository
from src.infrastructure.repositories.user_repository import UserRepository


class AcademicService:
    """Service layer enforcing academic hierarchy invariants and tenant isolation."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AcademicRepository(session)
        self.user_repo = UserRepository(session)
        self.audit = AuditService(session)

    # =========================================================================
    # DEPARTMENTS
    # =========================================================================
    async def create_department(
        self,
        institution_id: uuid.UUID,
        code: str,
        name: str,
        hod_user_id: Optional[uuid.UUID] = None,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> Department:
        clean_code = code.strip().upper()
        if not clean_code or not name.strip():
            raise ValidationError("Department code and name are required")

        existing = await self.repo.get_department_by_code(institution_id, clean_code)
        if existing:
            raise ConflictError(f"Department code '{clean_code}' already exists in this institution")

        if hod_user_id:
            hod_user = await self.user_repo.get_by_id(hod_user_id)
            if not hod_user or hod_user.institution_id != institution_id:
                raise ValidationError("HOD user not found or does not belong to this institution")

        dept = Department(
            institution_id=institution_id,
            code=clean_code,
            name=name.strip(),
            hod_user_id=hod_user_id,
        )
        created = await self.repo.create_department(dept)

        await self.audit.log_event(
            action="ACADEMIC_DEPARTMENT_CREATED",
            entity_name="Department",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={"code": created.code, "name": created.name},
        )
        return created

    async def list_departments(self, institution_id: uuid.UUID) -> List[Department]:
        return await self.repo.list_departments(institution_id)

    async def get_department(self, institution_id: uuid.UUID, dept_id: uuid.UUID) -> Department:
        dept = await self.repo.get_department_by_id(dept_id)
        if not dept or dept.institution_id != institution_id:
            raise NotFoundError("Department", str(dept_id))
        return dept

    # =========================================================================
    # PROGRAMS
    # =========================================================================
    async def create_program(
        self,
        institution_id: uuid.UUID,
        department_id: uuid.UUID,
        code: str,
        name: str,
        degree_level: str = "UNDERGRADUATE",
        total_semesters: int = 8,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> Program:
        clean_code = code.strip().upper()
        if not clean_code or not name.strip():
            raise ValidationError("Program code and name are required")
        if total_semesters < 1:
            raise ValidationError("Total semesters must be at least 1")

        # Verify department belongs to this institution
        await self.get_department(institution_id, department_id)

        existing = await self.repo.get_program_by_code(institution_id, clean_code)
        if existing:
            raise ConflictError(f"Program code '{clean_code}' already exists in this institution")

        program = Program(
            institution_id=institution_id,
            department_id=department_id,
            code=clean_code,
            name=name.strip(),
            degree_level=degree_level.upper(),
            total_semesters=total_semesters,
        )
        created = await self.repo.create_program(program)

        await self.audit.log_event(
            action="ACADEMIC_PROGRAM_CREATED",
            entity_name="Program",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={"code": created.code, "name": created.name, "department_id": str(department_id)},
        )
        return created

    async def list_programs(self, institution_id: uuid.UUID, department_id: Optional[uuid.UUID] = None) -> List[Program]:
        return await self.repo.list_programs(institution_id, department_id)

    async def get_program(self, institution_id: uuid.UUID, prog_id: uuid.UUID) -> Program:
        prog = await self.repo.get_program_by_id(prog_id)
        if not prog or prog.institution_id != institution_id:
            raise NotFoundError("Program", str(prog_id))
        return prog

    # =========================================================================
    # ACADEMIC YEARS & SEMESTERS
    # =========================================================================
    async def create_academic_year(
        self,
        institution_id: uuid.UUID,
        code: str,
        name: str,
        start_date: date,
        end_date: date,
        is_current: bool = False,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> AcademicYear:
        clean_code = code.strip().upper()
        if not clean_code or not name.strip():
            raise ValidationError("Academic year code and name are required")
        if start_date >= end_date:
            raise ValidationError("Academic year start_date must be strictly before end_date")

        existing = await self.repo.get_academic_year_by_code(institution_id, clean_code)
        if existing:
            raise ConflictError(f"Academic year code '{clean_code}' already exists in this institution")

        ay = AcademicYear(
            institution_id=institution_id,
            code=clean_code,
            name=name.strip(),
            start_date=start_date,
            end_date=end_date,
            is_current=is_current,
        )
        created = await self.repo.create_academic_year(ay)

        await self.audit.log_event(
            action="ACADEMIC_YEAR_CREATED",
            entity_name="AcademicYear",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={"code": created.code, "start_date": str(start_date), "end_date": str(end_date)},
        )
        return created

    async def list_academic_years(self, institution_id: uuid.UUID) -> List[AcademicYear]:
        return await self.repo.list_academic_years(institution_id)

    async def get_academic_year(self, institution_id: uuid.UUID, ay_id: uuid.UUID) -> AcademicYear:
        ay = await self.repo.get_academic_year_by_id(ay_id)
        if not ay or ay.institution_id != institution_id:
            raise NotFoundError("AcademicYear", str(ay_id))
        return ay

    async def create_semester(
        self,
        institution_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        term_number: int,
        name: str,
        start_date: date,
        end_date: date,
        status: str = "UPCOMING",
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> Semester:
        if term_number < 1:
            raise ValidationError("term_number must be at least 1")
        if start_date >= end_date:
            raise ValidationError("Semester start_date must be strictly before end_date")

        ay = await self.get_academic_year(institution_id, academic_year_id)

        # Enforce that semester dates fall within the parent academic year
        if start_date < ay.start_date or end_date > ay.end_date:
            raise ValidationError(
                f"Semester dates ({start_date} - {end_date}) must fall within parent Academic Year ({ay.start_date} - {ay.end_date})"
            )

        existing_sems = await self.repo.list_semesters(academic_year_id)
        for s in existing_sems:
            if s.term_number == term_number:
                raise ConflictError(f"Semester term number {term_number} already exists for this academic year")

        sem = Semester(
            institution_id=institution_id,
            academic_year_id=academic_year_id,
            term_number=term_number,
            name=name.strip(),
            start_date=start_date,
            end_date=end_date,
            status=status.upper(),
        )
        created = await self.repo.create_semester(sem)

        await self.audit.log_event(
            action="ACADEMIC_SEMESTER_CREATED",
            entity_name="Semester",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={"term_number": term_number, "name": name, "academic_year_id": str(academic_year_id)},
        )
        return created

    async def list_semesters(self, institution_id: uuid.UUID, academic_year_id: uuid.UUID) -> List[Semester]:
        await self.get_academic_year(institution_id, academic_year_id)
        return await self.repo.list_semesters(academic_year_id)

    # =========================================================================
    # BATCHES & SECTIONS
    # =========================================================================
    async def create_batch(
        self,
        institution_id: uuid.UUID,
        program_id: uuid.UUID,
        name: str,
        admission_year: int,
        graduation_year: int,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> Batch:
        if graduation_year < admission_year:
            raise ValidationError("graduation_year must be greater than or equal to admission_year")

        await self.get_program(institution_id, program_id)

        batch = Batch(
            institution_id=institution_id,
            program_id=program_id,
            name=name.strip(),
            admission_year=admission_year,
            graduation_year=graduation_year,
        )
        created = await self.repo.create_batch(batch)

        await self.audit.log_event(
            action="ACADEMIC_BATCH_CREATED",
            entity_name="Batch",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={"name": name, "admission_year": admission_year, "graduation_year": graduation_year},
        )
        return created

    async def list_batches(self, institution_id: uuid.UUID, program_id: Optional[uuid.UUID] = None) -> List[Batch]:
        return await self.repo.list_batches(institution_id, program_id)

    async def get_batch(self, institution_id: uuid.UUID, batch_id: uuid.UUID) -> Batch:
        batch = await self.repo.get_batch_by_id(batch_id)
        if not batch or batch.institution_id != institution_id:
            raise NotFoundError("Batch", str(batch_id))
        return batch

    async def create_section(
        self,
        institution_id: uuid.UUID,
        batch_id: uuid.UUID,
        name: str,
        capacity: int = 60,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> Section:
        if capacity < 1:
            raise ValidationError("Section capacity must be greater than zero")

        await self.get_batch(institution_id, batch_id)

        section = Section(
            institution_id=institution_id,
            batch_id=batch_id,
            name=name.strip(),
            capacity=capacity,
        )
        created = await self.repo.create_section(section)

        await self.audit.log_event(
            action="ACADEMIC_SECTION_CREATED",
            entity_name="Section",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={"name": name, "batch_id": str(batch_id), "capacity": capacity},
        )
        return created

    async def list_sections(self, institution_id: uuid.UUID, batch_id: uuid.UUID) -> List[Section]:
        await self.get_batch(institution_id, batch_id)
        return await self.repo.list_sections(batch_id)

    # =========================================================================
    # COURSE CATALOG & OFFERINGS
    # =========================================================================
    async def create_course(
        self,
        institution_id: uuid.UUID,
        department_id: uuid.UUID,
        code: str,
        title: str,
        credits: float = 3.0,
        course_type: str = "THEORY",
        course_metadata: Optional[Dict[str, Any]] = None,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> Course:
        clean_code = code.strip().upper()
        if not clean_code or not title.strip():
            raise ValidationError("Course code and title are required")
        if credits < 0:
            raise ValidationError("Course credits cannot be negative")

        await self.get_department(institution_id, department_id)

        existing = await self.repo.get_course_by_code(institution_id, clean_code)
        if existing:
            raise ConflictError(f"Course with code '{clean_code}' already exists in this institution")

        course = Course(
            institution_id=institution_id,
            department_id=department_id,
            code=clean_code,
            title=title.strip(),
            credits=credits,
            course_type=course_type.upper(),
            course_metadata=course_metadata or {},
        )
        created = await self.repo.create_course(course)

        await self.audit.log_event(
            action="ACADEMIC_COURSE_CREATED",
            entity_name="Course",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={"code": created.code, "title": created.title, "credits": credits},
        )
        return created

    async def list_courses(self, institution_id: uuid.UUID, department_id: Optional[uuid.UUID] = None) -> List[Course]:
        return await self.repo.list_courses(institution_id, department_id)

    async def get_course(self, institution_id: uuid.UUID, course_id: uuid.UUID) -> Course:
        course = await self.repo.get_course_by_id(course_id)
        if not course or course.institution_id != institution_id:
            raise NotFoundError("Course", str(course_id))
        return course

    async def create_course_offering(
        self,
        institution_id: uuid.UUID,
        course_id: uuid.UUID,
        academic_year_id: uuid.UUID,
        semester_id: uuid.UUID,
        section_id: Optional[uuid.UUID] = None,
        status: str = "PLANNED",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> CourseOffering:
        await self.get_course(institution_id, course_id)
        await self.get_academic_year(institution_id, academic_year_id)
        sem = await self.repo.get_semester_by_id(semester_id)
        if not sem or sem.institution_id != institution_id or sem.academic_year_id != academic_year_id:
            raise ValidationError("Semester not found or does not belong to specified academic year")

        if section_id:
            section = await self.repo.get_section_by_id(section_id)
            if not section or section.institution_id != institution_id:
                raise ValidationError("Section not found or does not belong to this institution")

        offering = CourseOffering(
            institution_id=institution_id,
            course_id=course_id,
            academic_year_id=academic_year_id,
            semester_id=semester_id,
            section_id=section_id,
            status=status.upper(),
            start_date=start_date,
            end_date=end_date,
        )
        created = await self.repo.create_course_offering(offering)

        await self.audit.log_event(
            action="ACADEMIC_OFFERING_CREATED",
            entity_name="CourseOffering",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={
                "course_id": str(course_id),
                "semester_id": str(semester_id),
                "section_id": str(section_id) if section_id else None,
            },
        )
        return created

    async def list_course_offerings(
        self, institution_id: uuid.UUID, semester_id: Optional[uuid.UUID] = None
    ) -> List[CourseOffering]:
        return await self.repo.list_course_offerings(institution_id, semester_id)

    async def get_course_offering(self, institution_id: uuid.UUID, offering_id: uuid.UUID) -> CourseOffering:
        offering = await self.repo.get_course_offering_by_id(offering_id)
        if not offering or offering.institution_id != institution_id:
            raise NotFoundError("CourseOffering", str(offering_id))
        return offering

    # =========================================================================
    # TEACHING ASSIGNMENTS & STUDENT ENROLLMENTS
    # =========================================================================
    async def assign_faculty(
        self,
        institution_id: uuid.UUID,
        course_offering_id: uuid.UUID,
        faculty_user_id: uuid.UUID,
        role_type: str = "PRIMARY_INSTRUCTOR",
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> TeachingAssignment:
        await self.get_course_offering(institution_id, course_offering_id)

        faculty_user = await self.user_repo.get_by_id(faculty_user_id)
        if not faculty_user or faculty_user.institution_id != institution_id:
            raise ValidationError("Faculty user not found or does not belong to this institution")

        existing = await self.repo.get_teaching_assignment(course_offering_id, faculty_user_id)
        if existing:
            raise ConflictError("Faculty user is already assigned to this course offering")

        assignment = TeachingAssignment(
            course_offering_id=course_offering_id,
            faculty_user_id=faculty_user_id,
            role_type=role_type.upper(),
        )
        created = await self.repo.assign_faculty(assignment)

        await self.audit.log_event(
            action="ACADEMIC_FACULTY_ASSIGNED",
            entity_name="TeachingAssignment",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={
                "offering_id": str(course_offering_id),
                "faculty_user_id": str(faculty_user_id),
                "role_type": role_type,
            },
        )
        return created

    async def enroll_student(
        self,
        institution_id: uuid.UUID,
        course_offering_id: uuid.UUID,
        student_user_id: uuid.UUID,
        actor_user_id: Optional[uuid.UUID] = None,
    ) -> StudentEnrollment:
        offering = await self.get_course_offering(institution_id, course_offering_id)

        student_user = await self.user_repo.get_by_id(student_user_id)
        if not student_user or student_user.institution_id != institution_id:
            raise ValidationError("Student user not found or does not belong to this institution")

        existing = await self.repo.get_enrollment(course_offering_id, student_user_id)
        if existing:
            raise ConflictError("Student is already enrolled in this course offering")

        # Capacity check if offering has a section
        if offering.section_id:
            section = await self.repo.get_section_by_id(offering.section_id)
            if section:
                current_enrollments = await self.repo.list_offering_enrollments(course_offering_id)
                if len(current_enrollments) >= section.capacity:
                    raise ValidationError(f"Section capacity of {section.capacity} reached for this offering")

        enrollment = StudentEnrollment(
            institution_id=institution_id,
            course_offering_id=course_offering_id,
            student_user_id=student_user_id,
            enrollment_status="ENROLLED",
        )
        created = await self.repo.enroll_student(enrollment)

        await self.audit.log_event(
            action="ACADEMIC_STUDENT_ENROLLED",
            entity_name="StudentEnrollment",
            entity_id=created.id,
            institution_id=institution_id,
            actor_user_id=actor_user_id,
            new_values={"offering_id": str(course_offering_id), "student_user_id": str(student_user_id)},
        )
        return created

    async def list_offering_enrollments(
        self, institution_id: uuid.UUID, course_offering_id: uuid.UUID
    ) -> List[StudentEnrollment]:
        await self.get_course_offering(institution_id, course_offering_id)
        return await self.repo.list_offering_enrollments(course_offering_id)
