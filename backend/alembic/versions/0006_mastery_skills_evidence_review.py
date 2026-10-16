"""0006_mastery_skills_evidence_review

Revision ID: 0006_mastery_skills_evidence_review
Revises: 0005_assessment_question_bank_grading
Create Date: 2026-10-15 18:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0006_mastery_skills_evidence_review'
down_revision: Union[str, None] = '0005_assessment_question_bank_grading'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Concepts
    op.create_table(
        'concepts',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('department_id', sa.Uuid(as_uuid=True), sa.ForeignKey('departments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('course_id', sa.Uuid(as_uuid=True), sa.ForeignKey('courses.id', ondelete='SET NULL'), nullable=True),
        sa.Column('parent_concept_id', sa.Uuid(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('bloom_level', sa.String(length=32), server_default='UNDERSTAND', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('institution_id', 'code', name='uq_concepts_institution_code'),
    )
    op.create_index('ix_concepts_institution_id', 'concepts', ['institution_id'])
    op.create_index('ix_concepts_inst_course', 'concepts', ['institution_id', 'course_id'])
    op.create_index('ix_concepts_inst_dept', 'concepts', ['institution_id', 'department_id'])

    # 2. Concept Prerequisites
    op.create_table(
        'concept_prerequisites',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_id', sa.Uuid(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('prerequisite_concept_id', sa.Uuid(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('concept_id', 'prerequisite_concept_id', name='uq_concept_prerequisites_pair'),
    )
    op.create_index('ix_concept_prereq_inst', 'concept_prerequisites', ['institution_id', 'concept_id'])

    # 3. Learning Outcomes
    op.create_table(
        'learning_outcomes',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', sa.Uuid(as_uuid=True), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=True),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('statement', sa.Text(), nullable=False),
        sa.Column('bloom_level', sa.String(length=32), server_default='APPLY', nullable=False),
        sa.Column('concept_id', sa.Uuid(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('skill_id', sa.Uuid(as_uuid=True), sa.ForeignKey('skills.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('institution_id', 'code', name='uq_learning_outcomes_inst_code'),
    )
    op.create_index('ix_learning_outcomes_inst_course', 'learning_outcomes', ['institution_id', 'course_id'])

    # 4. Skills
    op.create_table(
        'skills',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('code', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('category', sa.String(length=64), nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('institution_id', 'code', name='uq_skills_institution_code'),
    )
    op.create_index('ix_skills_institution_id', 'skills', ['institution_id'])
    op.create_index('ix_skills_inst_cat', 'skills', ['institution_id', 'category'])

    # 5. ConceptSkills (Association)
    op.create_table(
        'concept_skills',
        sa.Column('concept_id', sa.Uuid(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), primary_key=True, nullable=False),
        sa.Column('skill_id', sa.Uuid(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('weight', sa.Float(), server_default='1.0', nullable=False),
    )
    op.create_index('ix_concept_skills_institution_id', 'concept_skills', ['institution_id'])

    # 6. Mastery Records
    op.create_table(
        'mastery_records',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', sa.Uuid(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('mastery_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('confidence_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('competency_level', sa.String(length=32), server_default='INSUFFICIENT_EVIDENCE', nullable=False),
        sa.Column('assessment_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('evidence_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('decay_factor', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('rule_version', sa.String(length=32), server_default='2026.1', nullable=False),
        sa.Column('calculation_provenance', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('is_stale', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('last_assessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('institution_id', 'student_user_id', 'skill_id', name='uq_mastery_inst_student_skill'),
    )
    op.create_index('ix_mastery_records_institution_id', 'mastery_records', ['institution_id'])
    op.create_index('ix_mastery_student_skill', 'mastery_records', ['student_user_id', 'skill_id', 'institution_id'])
    op.create_index('ix_mastery_inst_score', 'mastery_records', ['institution_id', 'mastery_score'])

    # 7. Learning Evidences
    op.create_table(
        'learning_evidences',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', sa.Uuid(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_id', sa.Uuid(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('evidence_type', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('artifact_url', sa.String(length=1024), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('verification_status', sa.String(length=32), server_default='PENDING', nullable=False),
        sa.Column('verified_by', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), server_default='', nullable=False),
        sa.Column('source_assessment_id', sa.Uuid(as_uuid=True), sa.ForeignKey('assessments.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_submission_id', sa.Uuid(as_uuid=True), sa.ForeignKey('submissions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_question_id', sa.Uuid(as_uuid=True), sa.ForeignKey('questions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_result_id', sa.Uuid(as_uuid=True), sa.ForeignKey('results.id', ondelete='SET NULL'), nullable=True),
        sa.Column('awarded_score', sa.Float(), nullable=True),
        sa.Column('max_score', sa.Float(), nullable=True),
        sa.Column('rule_version', sa.String(length=32), server_default='2026.1', nullable=False),
        sa.Column('idempotency_key', sa.String(length=255), nullable=True),
        sa.Column('is_finalized', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('idempotency_key', name='uq_learning_evidences_idempotency'),
    )
    op.create_index('ix_learning_evidences_institution_id', 'learning_evidences', ['institution_id'])
    op.create_index('ix_evidence_inst_student', 'learning_evidences', ['institution_id', 'student_user_id'])
    op.create_index('ix_evidence_inst_status', 'learning_evidences', ['institution_id', 'verification_status'])
    op.create_index('ix_evidence_source_result', 'learning_evidences', ['source_result_id', 'source_question_id'])

    # 8. Review Schedules (SM-2 Spaced Repetition)
    op.create_table(
        'review_schedules',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('concept_id', sa.Uuid(as_uuid=True), sa.ForeignKey('concepts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('interval_days', sa.Integer(), server_default='1', nullable=False),
        sa.Column('repetition_number', sa.Integer(), server_default='0', nullable=False),
        sa.Column('ease_factor', sa.Float(), server_default='2.5', nullable=False),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_completed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_review_schedules_institution_id', 'review_schedules', ['institution_id'])
    op.create_index('ix_review_sched_student', 'review_schedules', ['student_user_id', 'scheduled_for', 'is_completed'])

    # Apply PostgreSQL Row-Level Security
    if is_postgres:
        tables = [
            'concepts',
            'concept_prerequisites',
            'learning_outcomes',
            'skills',
            'concept_skills',
            'mastery_records',
            'learning_evidences',
            'review_schedules',
        ]
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

    tables = [
        'review_schedules',
        'learning_evidences',
        'mastery_records',
        'concept_skills',
        'skills',
        'learning_outcomes',
        'concept_prerequisites',
        'concepts',
    ]
    if is_postgres:
        for table in tables:
            op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")

    for table in tables:
        op.drop_table(table)
