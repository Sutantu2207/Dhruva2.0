"""0009_ai_gateway_conversations_audit

Revision ID: 0009_ai_gateway_conversations_audit
Revises: 0008_interventions_notifications_analytics
Create Date: 2026-10-20 15:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0009_ai_gateway_conversations_audit'
down_revision: Union[str, None] = '0008_interventions_notifications_analytics'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. AI Conversations
    op.create_table(
        'ai_conversations',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('context_type', sa.String(length=64), nullable=False),
        sa.Column('context_id', sa.String(length=128), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_ai_conversations_institution_id', 'ai_conversations', ['institution_id'])
    op.create_index('ix_ai_conversations_user_id', 'ai_conversations', ['user_id'])
    op.create_index('ix_ai_conversations_context_type', 'ai_conversations', ['context_type'])
    op.create_index('ix_ai_conversations_context_id', 'ai_conversations', ['context_id'])
    op.create_index('ix_ai_conv_inst_user', 'ai_conversations', ['institution_id', 'user_id'])
    op.create_index('ix_ai_conv_inst_context', 'ai_conversations', ['institution_id', 'context_type', 'context_id'])

    # 2. AI Messages
    op.create_table(
        'ai_messages',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('conversation_id', sa.Uuid(as_uuid=True), sa.ForeignKey('ai_conversations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('sender_role', sa.String(length=32), nullable=False),
        sa.Column('raw_content', sa.Text(), nullable=False),
        sa.Column('sanitized_content', sa.Text(), nullable=False),
        sa.Column('citations_json', sa.JSON(), nullable=False),
        sa.Column('model_name', sa.String(length=64), server_default='dhruva-grounded-v2', nullable=False),
        sa.Column('token_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('latency_ms', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_ai_messages_institution_id', 'ai_messages', ['institution_id'])
    op.create_index('ix_ai_messages_conversation_id', 'ai_messages', ['conversation_id'])
    op.create_index('ix_ai_msg_conv_created', 'ai_messages', ['conversation_id', 'created_at'])
    op.create_index('ix_ai_msg_inst_conv', 'ai_messages', ['institution_id', 'conversation_id'])

    # 3. AI Audit Logs
    op.create_table(
        'ai_audit_logs',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('prompt_hash', sa.String(length=64), nullable=False),
        sa.Column('pii_detected_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('safety_verdict', sa.String(length=32), server_default='PASS', nullable=False),
        sa.Column('tokens_used', sa.Integer(), server_default='0', nullable=False),
        sa.Column('cost_estimate', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('metadata_json', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_ai_audit_logs_institution_id', 'ai_audit_logs', ['institution_id'])
    op.create_index('ix_ai_audit_logs_user_id', 'ai_audit_logs', ['user_id'])
    op.create_index('ix_ai_audit_logs_action', 'ai_audit_logs', ['action'])
    op.create_index('ix_ai_audit_logs_prompt_hash', 'ai_audit_logs', ['prompt_hash'])
    op.create_index('ix_ai_audit_logs_safety_verdict', 'ai_audit_logs', ['safety_verdict'])
    op.create_index('ix_ai_audit_inst_user_created', 'ai_audit_logs', ['institution_id', 'user_id', 'created_at'])
    op.create_index('ix_ai_audit_verdict', 'ai_audit_logs', ['institution_id', 'safety_verdict'])

    # Row-Level Security
    if is_postgres:
        tables = [
            'ai_conversations',
            'ai_messages',
            'ai_audit_logs',
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
        'ai_audit_logs',
        'ai_messages',
        'ai_conversations',
    ]
    if is_postgres:
        for table in tables:
            op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")

    for table in tables:
        op.drop_table(table)
