"""0008_interventions_notifications_analytics

Revision ID: 0008_interventions_notifications_analytics
Revises: 0007_projects_portfolios_placement
Create Date: 2026-10-16 19:41:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0008_interventions_notifications_analytics'
down_revision: Union[str, None] = '0007_projects_portfolios_placement'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Interventions
    op.create_table(
        'interventions',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('faculty_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('intervention_type', sa.String(length=64), nullable=False),
        sa.Column('trigger_reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ASSIGNED', nullable=False),
        sa.Column('action_plan', sa.Text(), server_default='', nullable=False),
        sa.Column('notes', sa.Text(), server_default='', nullable=False),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('outcome_notes', sa.Text(), server_default='', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_interventions_institution_id', 'interventions', ['institution_id'])
    op.create_index('ix_interventions_student_status', 'interventions', ['student_user_id', 'status'])
    op.create_index('ix_interventions_inst_status', 'interventions', ['institution_id', 'status'])
    op.create_index('ix_interventions_faculty_status', 'interventions', ['faculty_user_id', 'status'])

    # 2. Notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recipient_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('actor_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('notification_type', sa.String(length=64), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('link_url', sa.String(length=512), server_default='', nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='0' if not is_postgres else 'false', nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_notifications_institution_id', 'notifications', ['institution_id'])
    op.create_index('ix_notifications_user_read', 'notifications', ['recipient_user_id', 'is_read', 'created_at'])
    op.create_index('ix_notifications_inst_user', 'notifications', ['institution_id', 'recipient_user_id'])

    # 3. Analytics Rollups
    op.create_table(
        'analytics_rollups',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('department_id', sa.Uuid(as_uuid=True), sa.ForeignKey('departments.id', ondelete='CASCADE'), nullable=True),
        sa.Column('rollup_type', sa.String(length=64), nullable=False),
        sa.Column('metrics_payload', sa.JSON(), nullable=False),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_rollups_institution_id', 'analytics_rollups', ['institution_id'])
    op.create_index('ix_rollups_inst_dept_type', 'analytics_rollups', ['institution_id', 'department_id', 'rollup_type'])
    op.create_index('ix_rollups_inst_computed', 'analytics_rollups', ['institution_id', 'computed_at'])

    # Row-Level Security
    if is_postgres:
        tables = [
            'interventions',
            'notifications',
            'analytics_rollups',
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
        'analytics_rollups',
        'notifications',
        'interventions',
    ]
    if is_postgres:
        for table in tables:
            op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")

    for table in tables:
        op.drop_table(table)
