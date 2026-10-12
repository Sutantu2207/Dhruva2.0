"""Dhruva.AI V2 — Academic Hierarchy Schemas.

Pydantic schemas for request validation and response serialization.
Strictly types all domain models with full attribute mapping.
"""

import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =========================================================================
# DEPARTMENTS
# =========================================================================
class DepartmentCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=32, description="Unique department code, e.g. CSE")
    name: str = Field(min_length=2, max_length=128, description="Department name")
    hod_user_id: Optional[uuid.UUID] = Field(default=None, description="Assigned HOD User ID")


class DepartmentResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    code: str
    name: str
    hod_user_id: Optional[uuid.UUID] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# PROGRAMS
# =========================================================================
class ProgramCreateRequest(BaseModel):
    department_id: uuid.UUID
    code: str = Field(min_length=1, max_length=32, description="Unique program code, e.g. BTECH-CSE")
    name: str = Field(min_length=2, max_length=128, description="Program name, e.g. Bachelor of Technology in CSE")
    degree_level: str = Field(default="UNDERGRADUATE", description="UNDERGRADUATE | POSTGRADUATE | DIPLOMA | DOCTORAL")
    total_semesters: int = Field(default=8, ge=1, le=16)


class ProgramResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    department_id: uuid.UUID
    code: str
    name: str
    degree_level: str
    total_semesters: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# ACADEMIC YEARS & SEMESTERS
# =========================================================================
class AcademicYearCreateRequest(BaseModel):
    code: str = Field(min_length=4, max_length=32, description="Academic year identifier, e.g. 2026-2027")
    name: str = Field(min_length=2, max_length=64, description="Display name, e.g. Academic Year 2026-2027")
    start_date: date
    end_date: date
    is_current: bool = False


class AcademicYearResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    code: str
    name: str
    start_date: date
    end_date: date
    is_current: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SemesterCreateRequest(BaseModel):
    term_number: int = Field(ge=1, le=16, description="Semester or term index, e.g. 1, 2, 3")
    name: str = Field(min_length=2, max_length=64, description="e.g. Fall 2026 / Semester 1")
    start_date: date
    end_date: date
    status: str = Field(default="UPCOMING", description="UPCOMING | ONGOING | COMPLETED | ARCHIVED")


class SemesterResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    academic_year_id: uuid.UUID
    term_number: int
    name: str
    start_date: date
    end_date: date
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# BATCHES & SECTIONS
# =========================================================================
class BatchCreateRequest(BaseModel):
    program_id: uuid.UUID
    name: str = Field(min_length=2, max_length=64, description="Cohort name, e.g. Class of 2028")
    admission_year: int = Field(ge=1900, le=2100)
    graduation_year: int = Field(ge=1900, le=2100)


class BatchResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    program_id: uuid.UUID
    name: str
    admission_year: int
    graduation_year: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SectionCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=32, description="Section division, e.g. A, B, Section-1")
    capacity: int = Field(default=60, ge=1, le=500)


class SectionResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    batch_id: uuid.UUID
    name: str
    capacity: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# COURSES & OFFERINGS
# =========================================================================
class CourseCreateRequest(BaseModel):
    department_id: uuid.UUID
    code: str = Field(min_length=2, max_length=32, description="Course code, e.g. CS301")
    title: str = Field(min_length=2, max_length=255, description="Course title, e.g. Operating Systems")
    credits: float = Field(default=3.0, ge=0.0, le=30.0)
    course_type: str = Field(default="THEORY", description="THEORY | LAB | SEMINAR | PROJECT | ELECTIVE")
    course_metadata: Dict[str, Any] = Field(default_factory=dict)


class CourseResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    department_id: uuid.UUID
    code: str
    title: str
    credits: float
    course_type: str
    course_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CourseOfferingCreateRequest(BaseModel):
    course_id: uuid.UUID
    academic_year_id: uuid.UUID
    semester_id: uuid.UUID
    section_id: Optional[uuid.UUID] = None
    status: str = Field(default="PLANNED", description="PLANNED | OPEN | RUNNING | COMPLETED | ARCHIVED")
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class CourseOfferingResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    course_id: uuid.UUID
    academic_year_id: uuid.UUID
    semester_id: uuid.UUID
    section_id: Optional[uuid.UUID] = None
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# ASSIGNMENTS & ENROLLMENTS
# =========================================================================
class TeachingAssignmentCreateRequest(BaseModel):
    faculty_user_id: uuid.UUID
    role_type: str = Field(default="PRIMARY_INSTRUCTOR", description="PRIMARY_INSTRUCTOR | CO_INSTRUCTOR | TA")


class TeachingAssignmentResponse(BaseModel):
    id: uuid.UUID
    course_offering_id: uuid.UUID
    faculty_user_id: uuid.UUID
    role_type: str
    assigned_at: datetime

    class Config:
        from_attributes = True


class StudentEnrollmentCreateRequest(BaseModel):
    student_user_id: uuid.UUID


class StudentEnrollmentResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    course_offering_id: uuid.UUID
    student_user_id: uuid.UUID
    enrollment_status: str
    enrolled_at: datetime
    final_grade: Optional[float] = None

    class Config:
        from_attributes = True
