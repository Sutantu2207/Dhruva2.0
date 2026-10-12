"""Dhruva.AI V2 — Academic Repository.

Persistence layer for departments, programs, academic calendar, batches,
sections, courses, offerings, and student enrollments.
"""

import uuid
from typing import List, Optional
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
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


class AcademicRepository:
    """Async repository governing academic entities with strict institution scoping."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---------------- Department Operations ----------------
    async def create_department(self, department: Department) -> Department:
        self.session.add(department)
        await self.session.flush()
        return department

    async def get_department_by_id(self, dept_id: uuid.UUID) -> Optional[Department]:
        stmt = select(Department).where(Department.id == dept_id, Department.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_department_by_code(self, institution_id: uuid.UUID, code: str) -> Optional[Department]:
        stmt = select(Department).where(
            Department.institution_id == institution_id,
            Department.code == code.upper(),
            Department.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_departments(self, institution_id: uuid.UUID) -> List[Department]:
        stmt = select(Department).where(
            Department.institution_id == institution_id,
            Department.deleted_at.is_(None),
        ).order_by(Department.name.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ---------------- Program Operations ----------------
    async def create_program(self, program: Program) -> Program:
        self.session.add(program)
        await self.session.flush()
        return program

    async def get_program_by_id(self, prog_id: uuid.UUID) -> Optional[Program]:
        stmt = select(Program).where(Program.id == prog_id, Program.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_program_by_code(self, institution_id: uuid.UUID, code: str) -> Optional[Program]:
        stmt = select(Program).where(
            Program.institution_id == institution_id,
            Program.code == code.upper(),
            Program.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_programs(self, institution_id: uuid.UUID, department_id: Optional[uuid.UUID] = None) -> List[Program]:
        conditions = [Program.institution_id == institution_id, Program.deleted_at.is_(None)]
        if department_id:
            conditions.append(Program.department_id == department_id)
        stmt = select(Program).where(and_(*conditions)).order_by(Program.name.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ---------------- Academic Year & Semester Operations ----------------
    async def create_academic_year(self, ay: AcademicYear) -> AcademicYear:
        self.session.add(ay)
        await self.session.flush()
        return ay

    async def get_academic_year_by_id(self, ay_id: uuid.UUID) -> Optional[AcademicYear]:
        stmt = select(AcademicYear).where(AcademicYear.id == ay_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_academic_year_by_code(self, institution_id: uuid.UUID, code: str) -> Optional[AcademicYear]:
        stmt = select(AcademicYear).where(
            AcademicYear.institution_id == institution_id,
            AcademicYear.code == code,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_academic_years(self, institution_id: uuid.UUID) -> List[AcademicYear]:
        stmt = select(AcademicYear).where(AcademicYear.institution_id == institution_id).order_by(AcademicYear.start_date.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_semester(self, semester: Semester) -> Semester:
        self.session.add(semester)
        await self.session.flush()
        return semester

    async def get_semester_by_id(self, sem_id: uuid.UUID) -> Optional[Semester]:
        stmt = select(Semester).where(Semester.id == sem_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_semesters(self, academic_year_id: uuid.UUID) -> List[Semester]:
        stmt = select(Semester).where(Semester.academic_year_id == academic_year_id).order_by(Semester.term_number.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ---------------- Batch & Section Operations ----------------
    async def create_batch(self, batch: Batch) -> Batch:
        self.session.add(batch)
        await self.session.flush()
        return batch

    async def get_batch_by_id(self, batch_id: uuid.UUID) -> Optional[Batch]:
        stmt = select(Batch).where(Batch.id == batch_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_batches(self, institution_id: uuid.UUID, program_id: Optional[uuid.UUID] = None) -> List[Batch]:
        conditions = [Batch.institution_id == institution_id]
        if program_id:
            conditions.append(Batch.program_id == program_id)
        stmt = select(Batch).where(and_(*conditions)).order_by(Batch.admission_year.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_section(self, section: Section) -> Section:
        self.session.add(section)
        await self.session.flush()
        return section

    async def get_section_by_id(self, section_id: uuid.UUID) -> Optional[Section]:
        stmt = select(Section).where(Section.id == section_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_sections(self, batch_id: uuid.UUID) -> List[Section]:
        stmt = select(Section).where(Section.batch_id == batch_id).order_by(Section.name.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ---------------- Course & Offering Operations ----------------
    async def create_course(self, course: Course) -> Course:
        self.session.add(course)
        await self.session.flush()
        return course

    async def get_course_by_id(self, course_id: uuid.UUID) -> Optional[Course]:
        stmt = select(Course).where(Course.id == course_id, Course.deleted_at.is_(None))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_course_by_code(self, institution_id: uuid.UUID, code: str) -> Optional[Course]:
        stmt = select(Course).where(
            Course.institution_id == institution_id,
            Course.code == code.upper(),
            Course.deleted_at.is_(None),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_courses(self, institution_id: uuid.UUID, department_id: Optional[uuid.UUID] = None) -> List[Course]:
        conditions = [Course.institution_id == institution_id, Course.deleted_at.is_(None)]
        if department_id:
            conditions.append(Course.department_id == department_id)
        stmt = select(Course).where(and_(*conditions)).order_by(Course.code.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_course_offering(self, offering: CourseOffering) -> CourseOffering:
        self.session.add(offering)
        await self.session.flush()
        return offering

    async def get_course_offering_by_id(self, offering_id: uuid.UUID) -> Optional[CourseOffering]:
        stmt = select(CourseOffering).where(CourseOffering.id == offering_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_course_offerings(self, institution_id: uuid.UUID, semester_id: Optional[uuid.UUID] = None) -> List[CourseOffering]:
        conditions = [CourseOffering.institution_id == institution_id]
        if semester_id:
            conditions.append(CourseOffering.semester_id == semester_id)
        stmt = select(CourseOffering).where(and_(*conditions)).order_by(CourseOffering.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ---------------- Teaching & Enrollment Operations ----------------
    async def assign_faculty(self, assignment: TeachingAssignment) -> TeachingAssignment:
        self.session.add(assignment)
        await self.session.flush()
        return assignment

    async def get_teaching_assignment(self, offering_id: uuid.UUID, faculty_id: uuid.UUID) -> Optional[TeachingAssignment]:
        stmt = select(TeachingAssignment).where(
            TeachingAssignment.course_offering_id == offering_id,
            TeachingAssignment.faculty_user_id == faculty_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def enroll_student(self, enrollment: StudentEnrollment) -> StudentEnrollment:
        self.session.add(enrollment)
        await self.session.flush()
        return enrollment

    async def get_enrollment(self, offering_id: uuid.UUID, student_id: uuid.UUID) -> Optional[StudentEnrollment]:
        stmt = select(StudentEnrollment).where(
            StudentEnrollment.course_offering_id == offering_id,
            StudentEnrollment.student_user_id == student_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_offering_enrollments(self, offering_id: uuid.UUID) -> List[StudentEnrollment]:
        stmt = select(StudentEnrollment).where(StudentEnrollment.course_offering_id == offering_id).order_by(StudentEnrollment.enrolled_at.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ---------------- Profiles Operations ----------------
    async def create_student_profile(self, profile: StudentProfile) -> StudentProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def get_student_profile(self, user_id: uuid.UUID) -> Optional[StudentProfile]:
        stmt = select(StudentProfile).where(StudentProfile.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_student_by_roll(self, institution_id: uuid.UUID, roll_number: str) -> Optional[StudentProfile]:
        stmt = select(StudentProfile).where(
            StudentProfile.institution_id == institution_id,
            StudentProfile.roll_number == roll_number,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_faculty_profile(self, profile: FacultyProfile) -> FacultyProfile:
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def get_faculty_profile(self, user_id: uuid.UUID) -> Optional[FacultyProfile]:
        stmt = select(FacultyProfile).where(FacultyProfile.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
