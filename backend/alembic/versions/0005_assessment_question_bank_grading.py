"""0005_assessment_question_bank_grading

Revision ID: 0005_assessment_question_bank_grading
Revises: 0004_data_center_ingestion_provenance
Create Date: 2026-10-13 08:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0005_assessment_question_bank_grading'
down_revision: Union[str, None] = '0004_data_center_ingestion_provenance'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Question Banks
    op.create_table(
        'question_banks',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('department_id', sa.Uuid(as_uuid=True), sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('course_id', sa.Uuid(as_uuid=True), sa.ForeignKey('courses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('created_by', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_question_banks_institution_id', 'question_banks', ['institution_id'])
    op.create_index('ix_question_banks_inst_course', 'question_banks', ['institution_id', 'course_id'])
    op.create_index('ix_question_banks_inst_dept', 'question_banks', ['institution_id', 'department_id'])

    # 2. Questions
    op.create_table(
        'questions',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_bank_id', sa.Uuid(as_uuid=True), sa.ForeignKey('question_banks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_type', sa.String(length=32), nullable=False),
        sa.Column('prompt_text', sa.Text(), nullable=False),
        sa.Column('options', sa.JSON(), nullable=False),
        sa.Column('answer_key', sa.JSON(), nullable=False),
        sa.Column('points', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('difficulty', sa.String(length=16), server_default='MEDIUM', nullable=False),
        sa.Column('explanation', sa.Text(), server_default='', nullable=False),
        sa.Column('concept_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column('skill_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column('provenance_id', sa.Uuid(as_uuid=True), sa.ForeignKey('provenance_records.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_questions_institution_id', 'questions', ['institution_id'])
    op.create_index('ix_questions_bank_type', 'questions', ['question_bank_id', 'question_type'])
    op.create_index('ix_questions_inst_bank', 'questions', ['institution_id', 'question_bank_id'])

    # 3. Assessments
    op.create_table(
        'assessments',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_offering_id', sa.Uuid(as_uuid=True), sa.ForeignKey('course_offerings.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('instructions', sa.Text(), server_default='', nullable=False),
        sa.Column('assessment_type', sa.String(length=32), server_default='QUIZ', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='DRAFT', nullable=False),
        sa.Column('publish_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('total_points', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('passing_percentage', sa.Float(), server_default='40.0', nullable=False),
        sa.Column('max_attempts', sa.Integer(), server_default='1', nullable=False),
        sa.Column('created_by', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_assessments_institution_id', 'assessments', ['institution_id'])
    op.create_index('ix_assessments_inst_offering', 'assessments', ['institution_id', 'course_offering_id'])
    op.create_index('ix_assessments_offering_dates', 'assessments', ['course_offering_id', 'publish_at', 'due_at'])

    # 4. Assessment Questions (Association)
    op.create_table(
        'assessment_questions',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('assessment_id', sa.Uuid(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.Uuid(as_uuid=True), sa.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('points', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('sort_order', sa.Integer(), server_default='0', nullable=False),
        sa.UniqueConstraint('assessment_id', 'question_id', name='uq_assessment_question'),
    )
    op.create_index('ix_assessment_questions_order', 'assessment_questions', ['assessment_id', 'sort_order'])

    # 5. Submissions
    op.create_table(
        'submissions',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assessment_id', sa.Uuid(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('attempt_number', sa.Integer(), server_default='1', nullable=False),
        sa.Column('answers_payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='SUBMITTED', nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('assessment_id', 'student_user_id', 'attempt_number', name='uq_submission_attempt'),
    )
    op.create_index('ix_submissions_institution_id', 'submissions', ['institution_id'])
    op.create_index('ix_submissions_inst_student', 'submissions', ['institution_id', 'student_user_id'])
    op.create_index('ix_submissions_assessment_status', 'submissions', ['assessment_id', 'status'])

    # 6. Results
    op.create_table(
        'results',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('submission_id', sa.Uuid(as_uuid=True), sa.ForeignKey('submissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('raw_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('total_points', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('percentage', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('grade_letter', sa.String(length=8), nullable=True),
        sa.Column('is_passed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('itemized_breakdown', sa.JSON(), nullable=False),
        sa.Column('is_finalized', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('graded_by', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('graded_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('submission_id', name='uq_results_submission'),
    )
    op.create_index('ix_results_institution_id', 'results', ['institution_id'])
    op.create_index('ix_results_inst_submission', 'results', ['institution_id', 'submission_id'])

    # Apply PostgreSQL Row-Level Security
    if is_postgres:
        tables = ['question_banks', 'questions', 'assessments', 'submissions', 'results']
        for table in tables:
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
            op.execute(f"""
                CREATE POLICY {table}_tenant_isolation_policy ON {table}
                FOR ALL
                USING (
                    institution_id = NULLIF(current_setting('app.current_institution_id', true), '')::uuid
                );
            """)


def downgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    tables = ['results', 'submissions', 'assessment_questions', 'assessments', 'questions', 'question_banks']
    if is_postgres:
        for table in ['question_banks', 'questions', 'assessments', 'submissions', 'results']:
            op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")

    for table in tables:
        op.drop_table(table)
