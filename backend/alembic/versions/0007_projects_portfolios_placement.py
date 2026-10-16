"""0007_projects_portfolios_placement

Revision ID: 0007_projects_portfolios_placement
Revises: 0006_mastery_skills_evidence_review
Create Date: 2026-10-16 19:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007_projects_portfolios_placement'
down_revision: Union[str, None] = '0006_mastery_skills_evidence_review'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Projects
    op.create_table(
        'projects',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), server_default='', nullable=False),
        sa.Column('project_type', sa.String(length=32), server_default='COURSE_PROJECT', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='DRAFT', nullable=False),
        sa.Column('repository_url', sa.String(length=1024), server_default='', nullable=False),
        sa.Column('deployment_url', sa.String(length=1024), server_default='', nullable=False),
        sa.Column('start_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('end_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('contribution_details', sa.Text(), server_default='', nullable=False),
        sa.Column('verified_by', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verification_notes', sa.Text(), server_default='', nullable=False),
        sa.Column('revoked_by', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocation_reason', sa.Text(), server_default='', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_projects_institution_id', 'projects', ['institution_id'])
    op.create_index('ix_projects_student_inst', 'projects', ['student_user_id', 'institution_id'])
    op.create_index('ix_projects_inst_status', 'projects', ['institution_id', 'status'])

    # 2. Project Skills
    op.create_table(
        'project_skills',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.Uuid(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_id', sa.Uuid(as_uuid=True), sa.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False),
        sa.Column('contribution_weight', sa.Float(), server_default='1.0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('project_id', 'skill_id', name='uq_project_skills_project_skill'),
    )
    op.create_index('ix_project_skills_institution_id', 'project_skills', ['institution_id'])
    op.create_index('ix_project_skills_project_id', 'project_skills', ['project_id'])
    op.create_index('ix_project_skills_skill_id', 'project_skills', ['skill_id'])

    # 3. Project Evidences
    op.create_table(
        'project_evidences',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('project_id', sa.Uuid(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('evidence_id', sa.Uuid(as_uuid=True), sa.ForeignKey('learning_evidences.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('project_id', 'evidence_id', name='uq_project_evidences_project_ev'),
    )
    op.create_index('ix_project_evidences_institution_id', 'project_evidences', ['institution_id'])
    op.create_index('ix_project_evidences_project_id', 'project_evidences', ['project_id'])
    op.create_index('ix_project_evidences_evidence_id', 'project_evidences', ['evidence_id'])

    # 4. Portfolios
    op.create_table(
        'portfolios',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('slug', sa.String(length=128), nullable=False),
        sa.Column('headline', sa.String(length=255), server_default='', nullable=False),
        sa.Column('bio', sa.Text(), server_default='', nullable=False),
        sa.Column('visibility', sa.String(length=32), server_default='PRIVATE', nullable=False),
        sa.Column('is_published', sa.Boolean(), server_default='0' if not is_postgres else 'false', nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('curated_project_ids', sa.JSON(), nullable=False),
        sa.Column('featured_skill_ids', sa.JSON(), nullable=False),
        sa.Column('social_links', sa.JSON(), nullable=False),
        sa.Column('custom_domain', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('institution_id', 'student_user_id', name='uq_portfolios_inst_student'),
        sa.UniqueConstraint('institution_id', 'slug', name='uq_portfolios_inst_slug'),
    )
    op.create_index('ix_portfolios_institution_id', 'portfolios', ['institution_id'])
    op.create_index('ix_portfolios_visibility', 'portfolios', ['institution_id', 'visibility', 'is_published'])

    # 5. Career Goals
    op.create_table(
        'career_goals',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_role', sa.String(length=128), nullable=False),
        sa.Column('target_industry', sa.String(length=128), server_default='', nullable=False),
        sa.Column('target_companies', sa.JSON(), nullable=False),
        sa.Column('required_skill_ids', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_career_goals_institution_id', 'career_goals', ['institution_id'])
    op.create_index('ix_career_goals_student', 'career_goals', ['student_user_id', 'institution_id'])
    op.create_index('ix_career_goals_role', 'career_goals', ['institution_id', 'target_role'])

    # 6. Career Readiness
    op.create_table(
        'career_readiness',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('career_goal_id', sa.Uuid(as_uuid=True), sa.ForeignKey('career_goals.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_role', sa.String(length=128), nullable=False),
        sa.Column('readiness_score', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('matching_skills_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('total_required_skills', sa.Integer(), server_default='0', nullable=False),
        sa.Column('target_gap_analysis', sa.JSON(), nullable=False),
        sa.Column('rule_version', sa.String(length=32), server_default='2026.1', nullable=False),
        sa.Column('calculated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('calculation_provenance', sa.JSON(), nullable=False),
    )
    op.create_index('ix_career_readiness_institution_id', 'career_readiness', ['institution_id'])
    op.create_index('ix_readiness_inst_score', 'career_readiness', ['institution_id', 'readiness_score'])
    op.create_index('ix_readiness_student_goal', 'career_readiness', ['student_user_id', 'career_goal_id'])

    # Row-Level Security
    if is_postgres:
        tables = [
            'projects',
            'project_skills',
            'project_evidences',
            'portfolios',
            'career_goals',
            'career_readiness',
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
        'career_readiness',
        'career_goals',
        'portfolios',
        'project_evidences',
        'project_skills',
        'projects',
    ]
    if is_postgres:
        for table in tables:
            op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")

    for table in tables:
        op.drop_table(table)
