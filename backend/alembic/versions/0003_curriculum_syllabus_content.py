"""0003_curriculum_syllabus_content

Revision ID: 0003_curriculum_syllabus_content
Revises: 0002_academic_hierarchy
Create Date: 2026-10-12 20:20:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_curriculum_syllabus_content'
down_revision: Union[str, None] = '0002_academic_hierarchy'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Curriculums
    op.create_table(
        'curriculums',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('course_id', sa.Uuid(as_uuid=True), sa.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False),
        sa.Column('program_id', sa.Uuid(as_uuid=True), sa.ForeignKey('programs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('academic_year_id', sa.Uuid(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='SET NULL'), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='DRAFT', nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('learning_objectives', sa.JSON(), nullable=False),
        sa.Column('approved_by', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('provenance_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('course_id', 'version', name='uq_curriculum_course_version'),
    )
    op.create_index('ix_curriculums_institution_id', 'curriculums', ['institution_id'])
    op.create_index('ix_curriculums_course_id', 'curriculums', ['course_id'])
    op.create_index('ix_curriculums_inst_course', 'curriculums', ['institution_id', 'course_id'])
    op.create_index('ix_curriculums_status', 'curriculums', ['institution_id', 'status'])

    # 2. Modules
    op.create_table(
        'modules',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('curriculum_id', sa.Uuid(as_uuid=True), sa.ForeignKey('curriculums.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('estimated_hours', sa.Float(), server_default='10.0', nullable=False),
        sa.Column('learning_outcomes', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('curriculum_id', 'sequence_order', name='uq_module_curriculum_seq'),
    )
    op.create_index('ix_modules_institution_id', 'modules', ['institution_id'])
    op.create_index('ix_modules_curriculum_id', 'modules', ['curriculum_id'])
    op.create_index('ix_modules_curriculum_seq', 'modules', ['curriculum_id', 'sequence_order'])

    # 3. Lessons
    op.create_table(
        'lessons',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('module_id', sa.Uuid(as_uuid=True), sa.ForeignKey('modules.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content_markdown', sa.Text(), nullable=True),
        sa.Column('lesson_type', sa.String(length=32), server_default='THEORY', nullable=False),
        sa.Column('duration_minutes', sa.Integer(), server_default='60', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('module_id', 'sequence_order', name='uq_lesson_module_seq'),
    )
    op.create_index('ix_lessons_institution_id', 'lessons', ['institution_id'])
    op.create_index('ix_lessons_module_id', 'lessons', ['module_id'])
    op.create_index('ix_lessons_module_seq', 'lessons', ['module_id', 'sequence_order'])

    # 4. Learning Resources
    op.create_table(
        'learning_resources',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('lesson_id', sa.Uuid(as_uuid=True), sa.ForeignKey('lessons.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('resource_type', sa.String(length=32), server_default='DOCUMENT', nullable=False),
        sa.Column('storage_uri', sa.String(length=512), nullable=True),
        sa.Column('external_url', sa.String(length=512), nullable=True),
        sa.Column('resource_metadata', sa.JSON(), nullable=False),
        sa.Column('provenance_id', sa.Uuid(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_learning_resources_institution_id', 'learning_resources', ['institution_id'])
    op.create_index('ix_learning_resources_lesson_id', 'learning_resources', ['lesson_id'])

    # Apply PostgreSQL Row-Level Security
    if is_postgres:
        tables = ['curriculums', 'modules', 'lessons', 'learning_resources']
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

    tables = ['learning_resources', 'lessons', 'modules', 'curriculums']
    if is_postgres:
        for table in tables:
            op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")

    for table in tables:
        op.drop_table(table)
