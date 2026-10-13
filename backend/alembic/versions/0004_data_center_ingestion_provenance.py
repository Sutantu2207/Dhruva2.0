"""0004_data_center_ingestion_provenance

Revision ID: 0004_data_center_ingestion_provenance
Revises: 0003_curriculum_syllabus_content
Create Date: 2026-10-12 21:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_data_center_ingestion_provenance'
down_revision: Union[str, None] = '0003_curriculum_syllabus_content'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    is_postgres = bind.dialect.name == "postgresql"

    # 1. Data Sources
    op.create_table(
        'data_sources',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('source_type', sa.String(length=64), server_default='CSV_UPLOAD', nullable=False),
        sa.Column('connection_details', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=32), server_default='ACTIVE', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_data_sources_institution_id', 'data_sources', ['institution_id'])
    op.create_index('ix_data_sources_inst_type', 'data_sources', ['institution_id', 'source_type'])

    # 2. Import Batches
    op.create_table(
        'import_batches',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('data_source_id', sa.Uuid(as_uuid=True), sa.ForeignKey('data_sources.id', ondelete='SET NULL'), nullable=True),
        sa.Column('batch_number', sa.String(length=64), nullable=False),
        sa.Column('original_file_name', sa.String(length=255), nullable=False),
        sa.Column('file_sha256', sa.String(length=64), nullable=False),
        sa.Column('storage_uri', sa.String(length=512), nullable=False),
        sa.Column('file_size_bytes', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('mime_type', sa.String(length=128), server_default='text/csv', nullable=False),
        sa.Column('total_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('valid_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('warning_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_records', sa.Integer(), server_default='0', nullable=False),
        sa.Column('status', sa.String(length=32), server_default='UPLOADED', nullable=False),
        sa.Column('target_domain', sa.String(length=64), server_default='STUDENTS', nullable=False),
        sa.Column('uploaded_by', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('error_summary', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('batch_number', name='uq_import_batches_batch_number'),
    )
    op.create_index('ix_import_batches_institution_id', 'import_batches', ['institution_id'])
    op.create_index('ix_import_batches_status', 'import_batches', ['status'])
    op.create_index('ix_import_batches_sha', 'import_batches', ['file_sha256'])
    op.create_index('ix_import_batches_inst_status', 'import_batches', ['institution_id', 'status'])
    op.create_index('ix_import_batches_inst_created', 'import_batches', ['institution_id', 'created_at'])

    # 3. Staged Records
    op.create_table(
        'staged_records',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('import_batch_id', sa.Uuid(as_uuid=True), sa.ForeignKey('import_batches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('row_index', sa.Integer(), nullable=False),
        sa.Column('target_entity_type', sa.String(length=64), server_default='STUDENT', nullable=False),
        sa.Column('raw_payload', sa.JSON(), nullable=False),
        sa.Column('normalized_payload', sa.JSON(), nullable=False),
        sa.Column('extraction_coordinate', sa.String(length=128), server_default='', nullable=False),
        sa.Column('stage_status', sa.String(length=32), server_default='PENDING', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_staged_records_institution_id', 'staged_records', ['institution_id'])
    op.create_index('ix_staged_records_batch_id', 'staged_records', ['import_batch_id'])
    op.create_index('ix_staged_records_batch_status', 'staged_records', ['import_batch_id', 'stage_status'])
    op.create_index('ix_staged_records_inst_target', 'staged_records', ['institution_id', 'target_entity_type'])

    # 4. Validation Results
    op.create_table(
        'validation_results',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('staged_record_id', sa.Uuid(as_uuid=True), sa.ForeignKey('staged_records.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rule_code', sa.String(length=64), nullable=False),
        sa.Column('severity', sa.String(length=16), server_default='ERROR', nullable=False),
        sa.Column('field_name', sa.String(length=128), server_default='', nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('context', sa.JSON(), nullable=False),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_validation_results_institution_id', 'validation_results', ['institution_id'])
    op.create_index('ix_validation_results_record_id', 'validation_results', ['staged_record_id'])
    op.create_index('ix_validation_results_record_sev', 'validation_results', ['staged_record_id', 'severity'])

    # 5. Approvals
    op.create_table(
        'approvals',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('import_batch_id', sa.Uuid(as_uuid=True), sa.ForeignKey('import_batches.id', ondelete='CASCADE'), nullable=False),
        sa.Column('staged_record_id', sa.Uuid(as_uuid=True), sa.ForeignKey('staged_records.id', ondelete='CASCADE'), nullable=True),
        sa.Column('reviewer_user_id', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('decision', sa.String(length=32), server_default='APPROVED', nullable=False),
        sa.Column('digital_signature', sa.String(length=255), server_default='', nullable=False),
        sa.Column('notes', sa.Text(), server_default='', nullable=False),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_approvals_institution_id', 'approvals', ['institution_id'])
    op.create_index('ix_approvals_batch_id', 'approvals', ['import_batch_id'])
    op.create_index('ix_approvals_inst_batch', 'approvals', ['institution_id', 'import_batch_id'])

    # 6. Provenance Records
    op.create_table(
        'provenance_records',
        sa.Column('id', sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('institution_id', sa.Uuid(as_uuid=True), sa.ForeignKey('institutions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('authoritative_table', sa.String(length=64), nullable=False),
        sa.Column('authoritative_record_id', sa.Uuid(as_uuid=True), nullable=False),
        sa.Column('import_batch_id', sa.Uuid(as_uuid=True), sa.ForeignKey('import_batches.id', ondelete='SET NULL'), nullable=True),
        sa.Column('staged_record_id', sa.Uuid(as_uuid=True), sa.ForeignKey('staged_records.id', ondelete='SET NULL'), nullable=True),
        sa.Column('approved_by', sa.Uuid(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('source_type', sa.String(length=64), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_sha256', sa.String(length=64), nullable=False),
        sa.Column('coordinate_reference', sa.String(length=128), server_default='', nullable=False),
        sa.Column('snapshot_payload', sa.JSON(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_provenance_institution_id', 'provenance_records', ['institution_id'])
    op.create_index('ix_provenance_authoritative', 'provenance_records', ['authoritative_table', 'authoritative_record_id'])
    op.create_index('ix_provenance_inst_target', 'provenance_records', ['institution_id', 'authoritative_table', 'authoritative_record_id'])

    # Apply PostgreSQL Row-Level Security
    if is_postgres:
        tables = ['data_sources', 'import_batches', 'staged_records', 'validation_results', 'approvals', 'provenance_records']
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

    tables = ['provenance_records', 'approvals', 'validation_results', 'staged_records', 'import_batches', 'data_sources']
    if is_postgres:
        for table in tables:
            op.execute(f"DROP POLICY IF EXISTS {table}_tenant_isolation_policy ON {table};")

    for table in tables:
        op.drop_table(table)
