"""Dhruva.AI V2 — Academic Hierarchy & Course Catalog Models.

Defines the normalized academic organizational domain:
- Department: Institutional academic department (e.g. Computer Science)
- Program: Degree program (e.g. B.Tech in CSE)
- AcademicYear: Academic calendar year (e.g. 2026-2027)
- Semester: Term/semester within an academic year
- Batch: Student intake cohort (e.g. Class of 2027)
- Section: Division/class within a batch
- Course: Master catalog course (e.g. CS301 - Operating Systems)
- CourseOffering: Scheduled course section in a specific academic term
- TeachingAssignment: Faculty assigned to teach a course offering
- StudentEnrollment: Student enrolled in a course offering
- StudentProfile: Academic profile extension linked to core User
- FacultyProfile: Academic profile extension linked to core User
"""

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.persistence.postgres.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utc_now,
)


class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Institutional academic department."""

    __tablename__ = "departments"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    hod_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    programs: Mapped[List["Program"]] = relationship("Program", back_populates="department", cascade="all, delete-orphan", lazy="selectin")
    courses: Mapped[List["Course"]] = relationship("Course", back_populates="department", cascade="all, delete-orphan", lazy="selectin")
    faculty_profiles: Mapped[List["FacultyProfile"]] = relationship("FacultyProfile", back_populates="department", lazy="selectin")
    student_profiles: Mapped[List["StudentProfile"]] = relationship("StudentProfile", back_populates="department", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_dept_institution_code"),
        Index("ix_departments_inst_code", "institution_id", "code"),
    )

    def __repr__(self) -> str:
        return f"<Department(id={self.id}, code={self.code}, name={self.name})>"


class Program(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Academic degree program (e.g. B.Tech Computer Science)."""

    __tablename__ = "programs"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    degree_level: Mapped[str] = mapped_column(String(32), default="UNDERGRADUATE", nullable=False)
    total_semesters: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="programs", lazy="selectin")
    batches: Mapped[List["Batch"]] = relationship("Batch", back_populates="program", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_program_institution_code"),
        Index("ix_programs_inst_dept", "institution_id", "department_id"),
    )

    def __repr__(self) -> str:
        return f"<Program(id={self.id}, code={self.code}, name={self.name})>"


class AcademicYear(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Academic calendar year (e.g. 2026-2027)."""

    __tablename__ = "academic_years"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    semesters: Mapped[List["Semester"]] = relationship("Semester", back_populates="academic_year", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_ay_institution_code"),
        Index("ix_academic_years_inst", "institution_id"),
    )

    def __repr__(self) -> str:
        return f"<AcademicYear(id={self.id}, code={self.code}, current={self.is_current})>"


class Semester(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Academic term / semester within an academic year."""

    __tablename__ = "semesters"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    term_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="UPCOMING", nullable=False)

    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", back_populates="semesters", lazy="selectin")
    offerings: Mapped[List["CourseOffering"]] = relationship("CourseOffering", back_populates="semester", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("academic_year_id", "term_number", name="uq_sem_ay_term"),
        Index("ix_semesters_inst_ay", "institution_id", "academic_year_id"),
    )

    def __repr__(self) -> str:
        return f"<Semester(id={self.id}, name={self.name}, status={self.status})>"


class Batch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Student admission cohort / batch."""

    __tablename__ = "batches"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    admission_year: Mapped[int] = mapped_column(Integer, nullable=False)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    program: Mapped["Program"] = relationship("Program", back_populates="batches", lazy="selectin")
    sections: Mapped[List["Section"]] = relationship("Section", back_populates="batch", cascade="all, delete-orphan", lazy="selectin")
    student_profiles: Mapped[List["StudentProfile"]] = relationship("StudentProfile", back_populates="batch", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("program_id", "name", name="uq_batch_program_name"),
        Index("ix_batches_inst_prog", "institution_id", "program_id"),
    )

    def __repr__(self) -> str:
        return f"<Batch(id={self.id}, name={self.name}, {self.admission_year}-{self.graduation_year})>"


class Section(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Class division / section within a batch."""

    __tablename__ = "sections"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(32), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=60, nullable=False)

    # Relationships
    batch: Mapped["Batch"] = relationship("Batch", back_populates="sections", lazy="selectin")
    student_profiles: Mapped[List["StudentProfile"]] = relationship("StudentProfile", back_populates="section", lazy="selectin")
    course_offerings: Mapped[List["CourseOffering"]] = relationship("CourseOffering", back_populates="section", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("batch_id", "name", name="uq_section_batch_name"),
        Index("ix_sections_inst_batch", "institution_id", "batch_id"),
    )

    def __repr__(self) -> str:
        return f"<Section(id={self.id}, name={self.name}, cap={self.capacity})>"


class Course(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Institutional Master Course Catalog Entity."""

    __tablename__ = "courses"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    credits: Mapped[float] = mapped_column(Float, default=3.0, nullable=False)
    course_type: Mapped[str] = mapped_column(String(32), default="THEORY", nullable=False)
    course_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="courses", lazy="selectin")
    offerings: Mapped[List["CourseOffering"]] = relationship("CourseOffering", back_populates="course", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("institution_id", "code", name="uq_course_inst_code"),
        Index("ix_courses_inst_dept", "institution_id", "department_id"),
    )

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, code={self.code}, title={self.title})>"


class CourseOffering(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Scheduled course offering in a specific academic term and section."""

    __tablename__ = "course_offerings"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    semester_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("semesters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="PLANNED", nullable=False)
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="offerings", lazy="selectin")
    semester: Mapped["Semester"] = relationship("Semester", back_populates="offerings", lazy="selectin")
    section: Mapped[Optional["Section"]] = relationship("Section", back_populates="course_offerings", lazy="selectin")
    teaching_assignments: Mapped[List["TeachingAssignment"]] = relationship("TeachingAssignment", back_populates="course_offering", cascade="all, delete-orphan", lazy="selectin")
    enrollments: Mapped[List["StudentEnrollment"]] = relationship("StudentEnrollment", back_populates="course_offering", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        Index("ix_course_offerings_inst_sem", "institution_id", "semester_id"),
    )

    def __repr__(self) -> str:
        return f"<CourseOffering(id={self.id}, course_id={self.course_id}, status={self.status})>"


class TeachingAssignment(Base, UUIDPrimaryKeyMixin):
    """Faculty teaching assignment for a specific course offering."""

    __tablename__ = "teaching_assignments"

    course_offering_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("course_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    faculty_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role_type: Mapped[str] = mapped_column(String(32), default="PRIMARY_INSTRUCTOR", nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    course_offering: Mapped["CourseOffering"] = relationship("CourseOffering", back_populates="teaching_assignments", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("course_offering_id", "faculty_user_id", name="uq_ta_offering_faculty"),
    )

    def __repr__(self) -> str:
        return f"<TeachingAssignment(offering={self.course_offering_id}, faculty={self.faculty_user_id}, role={self.role_type})>"


class StudentEnrollment(Base, UUIDPrimaryKeyMixin):
    """Student enrollment in a course offering."""

    __tablename__ = "enrollments"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_offering_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("course_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enrollment_status: Mapped[str] = mapped_column(String(32), default="ENROLLED", nullable=False)
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    final_grade: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    course_offering: Mapped["CourseOffering"] = relationship("CourseOffering", back_populates="enrollments", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("course_offering_id", "student_user_id", name="uq_enrollment_offering_student"),
        Index("ix_enrollments_inst_student", "institution_id", "student_user_id"),
    )

    def __repr__(self) -> str:
        return f"<StudentEnrollment(offering={self.course_offering_id}, student={self.student_user_id}, status={self.enrollment_status})>"


class StudentProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Extended academic profile for student users."""

    __tablename__ = "students"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    section_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("sections.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    roll_number: Mapped[str] = mapped_column(String(64), nullable=False)
    admission_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    academic_status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="student_profiles", lazy="selectin")
    batch: Mapped[Optional["Batch"]] = relationship("Batch", back_populates="student_profiles", lazy="selectin")
    section: Mapped[Optional["Section"]] = relationship("Section", back_populates="student_profiles", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("institution_id", "roll_number", name="uq_student_inst_roll"),
        Index("ix_students_inst_dept", "institution_id", "department_id"),
    )

    def __repr__(self) -> str:
        return f"<StudentProfile(roll={self.roll_number}, dept={self.department_id}, status={self.academic_status})>"


class FacultyProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Extended academic profile for faculty users."""

    __tablename__ = "faculty"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    employee_id: Mapped[str] = mapped_column(String(64), nullable=False)
    designation: Mapped[str] = mapped_column(String(64), default="ASSISTANT_PROFESSOR", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)

    # Relationships
    department: Mapped["Department"] = relationship("Department", back_populates="faculty_profiles", lazy="selectin")

    __table_args__ = (
        UniqueConstraint("institution_id", "employee_id", name="uq_faculty_inst_empid"),
        Index("ix_faculty_inst_dept", "institution_id", "department_id"),
    )

    def __repr__(self) -> str:
        return f"<FacultyProfile(empid={self.employee_id}, designation={self.designation})>"
