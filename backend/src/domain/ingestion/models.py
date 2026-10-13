"""Dhruva.AI V2 — Ingestion, Staging, Approval & Provenance Domain Models.

Implements the 9-stage data ingestion pipeline:
Upload -> Extract -> Normalize -> Validate -> Stage -> Review -> Approve -> Publish -> Audit
with immutable, end-to-end data provenance tracking.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.infrastructure.persistence.postgres.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    utc_now,
)


class DataSource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Institutional Data Source registry (e.g. SIS export, CSV upload, LMS sync)."""

    __tablename__ = "data_sources"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(64),
        default="CSV_UPLOAD",
        nullable=False,
    )
    connection_details: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", nullable=False)

    # Relationships
    batches: Mapped[List["ImportBatch"]] = relationship(
        "ImportBatch",
        back_populates="data_source",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_data_sources_inst_type", "institution_id", "source_type"),
    )

    def __repr__(self) -> str:
        return f"<DataSource(id={self.id}, name={self.name}, type={self.source_type})>"


class ImportBatch(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Batch ingestion lifecycle tracker."""

    __tablename__ = "import_batches"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("data_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    batch_number: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    storage_uri: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(128), default="text/csv", nullable=False)
    
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    valid_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    status: Mapped[str] = mapped_column(
        String(32),
        default="UPLOADED",
        index=True,
        nullable=False,
    )
    target_domain: Mapped[str] = mapped_column(
        String(64),
        default="STUDENTS",
        nullable=False,
    )
    uploaded_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    error_summary: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    data_source: Mapped[Optional["DataSource"]] = relationship(
        "DataSource",
        back_populates="batches",
        lazy="selectin",
    )
    staged_records: Mapped[List["StagedRecord"]] = relationship(
        "StagedRecord",
        back_populates="import_batch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    approvals: Mapped[List["Approval"]] = relationship(
        "Approval",
        back_populates="import_batch",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    provenance_records: Mapped[List["ProvenanceRecord"]] = relationship(
        "ProvenanceRecord",
        back_populates="import_batch",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_import_batches_inst_status", "institution_id", "status"),
        Index("ix_import_batches_inst_created", "institution_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ImportBatch(id={self.id}, number={self.batch_number}, status={self.status})>"


class StagedRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Raw and normalized staged record isolated from live authoritative tables."""

    __tablename__ = "staged_records"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    import_batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    target_entity_type: Mapped[str] = mapped_column(
        String(64),
        default="STUDENT",
        nullable=False,
    )
    raw_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    normalized_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    extraction_coordinate: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    stage_status: Mapped[str] = mapped_column(
        String(32),
        default="PENDING",
        index=True,
        nullable=False,
    )

    # Relationships
    import_batch: Mapped["ImportBatch"] = relationship(
        "ImportBatch",
        back_populates="staged_records",
        lazy="selectin",
    )
    validation_results: Mapped[List["ValidationResult"]] = relationship(
        "ValidationResult",
        back_populates="staged_record",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_staged_records_batch_status", "import_batch_id", "stage_status"),
        Index("ix_staged_records_inst_target", "institution_id", "target_entity_type"),
    )

    def __repr__(self) -> str:
        return f"<StagedRecord(id={self.id}, batch={self.import_batch_id}, row={self.row_index}, status={self.stage_status})>"


class ValidationResult(Base, UUIDPrimaryKeyMixin):
    """Deterministic validation rule result linked to a staged record."""

    __tablename__ = "validation_results"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    staged_record_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("staged_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_code: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(16), default="ERROR", nullable=False)
    field_name: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    staged_record: Mapped["StagedRecord"] = relationship(
        "StagedRecord",
        back_populates="validation_results",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_validation_results_record_sev", "staged_record_id", "severity"),
    )

    def __repr__(self) -> str:
        return f"<ValidationResult(id={self.id}, code={self.rule_code}, severity={self.severity})>"


class Approval(Base, UUIDPrimaryKeyMixin):
    """Institutional sign-off record before moving staged data into authoritative tables."""

    __tablename__ = "approvals"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    import_batch_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    staged_record_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("staged_records.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    reviewer_user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    decision: Mapped[str] = mapped_column(String(32), default="APPROVED", nullable=False)
    digital_signature: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
    decided_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    import_batch: Mapped["ImportBatch"] = relationship(
        "ImportBatch",
        back_populates="approvals",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_approvals_inst_batch", "institution_id", "import_batch_id"),
    )

    def __repr__(self) -> str:
        return f"<Approval(id={self.id}, batch={self.import_batch_id}, decision={self.decision})>"


class ProvenanceRecord(Base, UUIDPrimaryKeyMixin):
    """Immutable provenance chain linking published live records to original ingest source."""

    __tablename__ = "provenance_records"

    institution_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    authoritative_table: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    authoritative_record_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        index=True,
        nullable=False,
    )
    import_batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("import_batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    staged_record_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("staged_records.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    coordinate_reference: Mapped[str] = mapped_column(String(128), default="", nullable=False)
    snapshot_payload: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )

    # Relationships
    import_batch: Mapped[Optional["ImportBatch"]] = relationship(
        "ImportBatch",
        back_populates="provenance_records",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_provenance_inst_target", "institution_id", "authoritative_table", "authoritative_record_id"),
    )

    def __repr__(self) -> str:
        return f"<ProvenanceRecord(id={self.id}, table={self.authoritative_table}, record_id={self.authoritative_record_id})>"
