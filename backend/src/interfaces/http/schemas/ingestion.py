"""Dhruva.AI V2 — Ingestion & Data Center API Schemas.

Pydantic schemas for request validation and response serialization.
Strictly types Data Sources, Import Batches, Staged Records, Validations, Approvals, and Provenance.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =========================================================================
# DATA SOURCES
# =========================================================================
class DataSourceCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255, description="Source registry name")
    source_type: str = Field(
        default="CSV_UPLOAD",
        description="CSV_UPLOAD | SPREADSHEET_UPLOAD | SIS_SYNC | LMS_EXPORT | EXTERNAL_API",
    )
    connection_details: Dict[str, Any] = Field(default_factory=dict)


class DataSourceResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    name: str
    source_type: str
    connection_details: Dict[str, Any] = Field(default_factory=dict)
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# VALIDATION RESULTS
# =========================================================================
class ValidationResultResponse(BaseModel):
    id: uuid.UUID
    staged_record_id: uuid.UUID
    rule_code: str
    severity: str
    field_name: str
    message: str
    context: Dict[str, Any] = Field(default_factory=dict)
    checked_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# STAGED RECORDS
# =========================================================================
class StagedRecordResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    import_batch_id: uuid.UUID
    row_index: int
    target_entity_type: str
    raw_payload: Dict[str, Any] = Field(default_factory=dict)
    normalized_payload: Dict[str, Any] = Field(default_factory=dict)
    extraction_coordinate: str
    stage_status: str
    created_at: datetime
    updated_at: datetime
    validation_results: List[ValidationResultResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# =========================================================================
# IMPORT BATCHES
# =========================================================================
class ImportBatchResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    data_source_id: Optional[uuid.UUID] = None
    batch_number: str
    original_file_name: str
    file_sha256: str
    storage_uri: str
    file_size_bytes: int
    mime_type: str
    total_records: int
    valid_records: int
    warning_records: int
    error_records: int
    status: str
    target_domain: str
    uploaded_by: Optional[uuid.UUID] = None
    error_summary: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# APPROVALS
# =========================================================================
class ApprovalRequest(BaseModel):
    decision: str = Field(description="APPROVED | REJECTED")
    digital_signature: str = Field(default="", description="Signer confirmation or signature")
    notes: Optional[str] = Field(default="", description="Optional review notes")


class ApprovalResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    import_batch_id: uuid.UUID
    reviewer_user_id: Optional[uuid.UUID] = None
    decision: str
    digital_signature: str
    notes: str
    decided_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# PROVENANCE RECORDS
# =========================================================================
class ProvenanceRecordResponse(BaseModel):
    id: uuid.UUID
    institution_id: uuid.UUID
    authoritative_table: str
    authoritative_record_id: uuid.UUID
    import_batch_id: Optional[uuid.UUID] = None
    staged_record_id: Optional[uuid.UUID] = None
    approved_by: Optional[uuid.UUID] = None
    source_type: str
    original_filename: str
    file_sha256: str
    coordinate_reference: str
    snapshot_payload: Dict[str, Any] = Field(default_factory=dict)
    published_at: datetime

    class Config:
        from_attributes = True


# =========================================================================
# TELEMETRY OVERVIEW
# =========================================================================
class DataCenterTelemetryResponse(BaseModel):
    total_batches: int
    pending_approval: int
    published_batches: int
    total_records: int
    valid_records: int
    warning_records: int
    error_records: int
    failure_rate_percent: float
    active_data_sources: int
    total_provenance_records: int
