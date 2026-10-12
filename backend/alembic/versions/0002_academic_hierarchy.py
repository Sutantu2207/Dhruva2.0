"""0002_academic_hierarchy

Revision ID: 0002_academic_hierarchy
Revises: 0001_core_foundation
Create Date: 2026-10-12 19:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_academic_hierarchy'
down_revision: Union[str, None] = '0001_core_foundation'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Departments
    op.create_table(
        'departments',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('hod_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('institution_id', 'code', name='uq_dept_institution_code'),
    )
    op.create_index('ix_departments_institution_id', 'departments', ['institution_id'])
    op.create_index('ix_departments_inst_code', 'departments', ['institution_id', 'code'])

    # 2. Programs
    op.create_table(
        'programs',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('department_id', sa.Uuid(as_uuid=True), sa.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('degree_level', sa.String(length=32), server_default='UNDERGRADUATE', nullable=False),
        sa.Column('total_semesters', sa.Integer(), server_default='8', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('institution_id', 'code', name='uq_program_institution_code'),
    )
    op.create_index('ix_programs_institution_id', 'programs', ['institution_id'])
    op.create_index('ix_programs_department_id', 'programs', ['department_id'])
    op.create_index('ix_programs_inst_dept', 'programs', ['institution_id', 'department_id'])

    # 3. Academic Years
    op.create_table(
        'academic_years',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('is_current', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('institution_id', 'code', name='uq_ay_institution_code'),
    )
    op.create_index('ix_academic_years_institution_id', 'academic_years', ['institution_id'])

    # 4. Semesters
    op.create_table(
        'semesters',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', sa.Uuid(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('term_number', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='UPCOMING', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('academic_year_id', 'term_number', name='uq_sem_ay_term'),
    )
    op.create_index('ix_semesters_institution_id', 'semesters', ['institution_id'])
    op.create_index('ix_semesters_academic_year_id', 'semesters', ['academic_year_id'])
    op.create_index('ix_semesters_inst_ay', 'semesters', ['institution_id', 'academic_year_id'])

    # 5. Batches
    op.create_table(
        'batches',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('program_id', sa.Uuid(as_uuid=True), sa.ForeignKey('programs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=64), nullable=False),
        sa.Column('admission_year', sa.Integer(), nullable=False),
        sa.Column('graduation_year', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('program_id', 'name', name='uq_batch_program_name'),
    )
    op.create_index('ix_batches_institution_id', 'batches', ['institution_id'])
    op.create_index('ix_batches_program_id', 'batches', ['program_id'])
    op.create_index('ix_batches_inst_prog', 'batches', ['institution_id', 'program_id'])

    # 6. Sections
    op.create_table(
        'sections',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('batch_id', sa.Uuid(as_uuid=True), sa.ForeignKey('batches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=32), nullable=False),
        sa.Column('capacity', sa.Integer(), server_default='60', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('batch_id', 'name', name='uq_section_batch_name'),
    )
    op.create_index('ix_sections_institution_id', 'sections', ['institution_id'])
    op.create_index('ix_sections_batch_id', 'sections', ['batch_id'])
    op.create_index('ix_sections_inst_batch', 'sections', ['institution_id', 'batch_id'])

    # 7. Courses
    op.create_table(
        'courses',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('department_id', sa.Uuid(as_uuid=True), sa.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('credits', sa.Float(), server_default='3.0', nullable=False),
        sa.Column('course_type', sa.String(length=32), server_default='THEORY', nullable=False),
        sa.Column('course_metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('institution_id', 'code', name='uq_course_inst_code'),
    )
    op.create_index('ix_courses_institution_id', 'courses', ['institution_id'])
    op.create_index('ix_courses_department_id', 'courses', ['department_id'])
    op.create_index('ix_courses_inst_dept', 'courses', ['institution_id', 'department_id'])

    # 8. Course Offerings
    op.create_table(
        'course_offerings',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', sa.Uuid(as_uuid=True), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', sa.Uuid(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('semester_id', sa.Uuid(as_uuid=True), sa.ForeignKey('semesters.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', sa.Uuid(as_uuid=True), sa.ForeignKey('sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', sa.String(length=32), server_default='PLANNED', nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_course_offerings_institution_id', 'course_offerings', ['institution_id'])
    op.create_index('ix_course_offerings_course_id', 'course_offerings', ['course_id'])
    op.create_index('ix_course_offerings_semester_id', 'course_offerings', ['semester_id'])
    op.create_index('ix_course_offerings_section_id', 'course_offerings', ['section_id'])
    op.create_index('ix_course_offerings_inst_sem', 'course_offerings', ['institution_id', 'semester_id'])

    # 9. Teaching Assignments
    op.create_table(
        'teaching_assignments',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('course_offering_id', sa.Uuid(as_uuid=True), sa.ForeignKey('course_offerings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('faculty_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role_type', sa.String(length=32), server_default='PRIMARY_INSTRUCTOR', nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('course_offering_id', 'faculty_user_id', name='uq_ta_offering_faculty'),
    )
    op.create_index('ix_teaching_assignments_course_offering_id', 'teaching_assignments', ['course_offering_id'])
    op.create_index('ix_teaching_assignments_faculty_user_id', 'teaching_assignments', ['faculty_user_id'])

    # 10. Student Enrollments
    op.create_table(
        'enrollments',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_offering_id', sa.Uuid(as_uuid=True), sa.ForeignKey('course_offerings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('enrollment_status', sa.String(length=32), server_default='ENROLLED', nullable=False),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('final_grade', sa.Float(), nullable=True),
        sa.UniqueConstraint('course_offering_id', 'student_user_id', name='uq_enrollment_offering_student'),
    )
    op.create_index('ix_enrollments_institution_id', 'enrollments', ['institution_id'])
    op.create_index('ix_enrollments_course_offering_id', 'enrollments', ['course_offering_id'])
    op.create_index('ix_enrollments_student_user_id', 'enrollments', ['student_user_id'])
    op.create_index('ix_enrollments_inst_student', 'enrollments', ['institution_id', 'student_user_id'])

    # 11. Student Profiles
    op.create_table(
        'students',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('department_id', sa.Uuid(as_uuid=True), sa.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('program_id', sa.Uuid(as_uuid=True), sa.ForeignKey('programs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('batch_id', sa.Uuid(as_uuid=True), sa.ForeignKey('batches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('section_id', sa.Uuid(as_uuid=True), sa.ForeignKey('sections.id', ondelete='SET NULL'), nullable=True),
        sa.Column('roll_number', sa.String(length=64), nullable=False),
        sa.Column('admission_date', sa.Date(), nullable=True),
        sa.Column('academic_status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('institution_id', 'roll_number', name='uq_student_inst_roll'),
    )
    op.create_index('ix_students_institution_id', 'students', ['institution_id'])
    op.create_index('ix_students_department_id', 'students', ['department_id'])
    op.create_index('ix_students_program_id', 'students', ['program_id'])
    op.create_index('ix_students_batch_id', 'students', ['batch_id'])
    op.create_index('ix_students_section_id', 'students', ['section_id'])
    op.create_index('ix_students_inst_dept', 'students', ['institution_id', 'department_id'])

    # 12. Faculty Profiles
    op.create_table(
        'faculty',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('department_id', sa.Uuid(as_uuid=True), sa.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('employee_id', sa.String(length=64), nullable=False),
        sa.Column('designation', sa.String(length=64), server_default='ASSISTANT_PROFESSOR', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('institution_id', 'employee_id', name='uq_faculty_inst_empid'),
    )
    op.create_index('ix_faculty_institution_id', 'faculty', ['institution_id'])
    op.create_index('ix_faculty_department_id', 'faculty', ['department_id'])
    op.create_index('ix_faculty_inst_dept', 'faculty', ['institution_id', 'department_id'])

    # PostgreSQL Row-Level Security Policies
    if is_postgres:
        tenant_tables = [
            'departments', 'programs', 'academic_years', 'semesters',
            'batches', 'sections', 'courses', 'course_offerings',
            'enrollments', 'students', 'faculty'
        ]
        for tbl in tenant_tables:
            op.execute(f"ALTER TABLE {tbl} ENABLE ROW LEVEL SECURITY;")
            op.execute(f"""
                CREATE POLICY tenant_isolation_policy ON {tbl}
                AS RESTRICTIVE
                FOR ALL
                USING (
                    institution_id = NULLIF(current_setting('app.current_institution_id', true), '')::uuid
                );
            """)


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    if is_postgres:
        tenant_tables = [
            'departments', 'programs', 'academic_years', 'semesters',
            'batches', 'sections', 'courses', 'course_offerings',
            'enrollments', 'students', 'faculty'
        ]
        for tbl in tenant_tables:
            op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {tbl};")

    op.drop_table('faculty')
    op.drop_table('students')
    op.drop_table('enrollments')
    op.drop_table('teaching_assignments')
    op.drop_table('course_offerings')
    op.drop_table('courses')
    op.drop_table('sections')
    op.drop_table('batches')
    op.drop_table('semesters')
    op.drop_table('academic_years')
    op.drop_table('programs')
    op.drop_table('departments')
