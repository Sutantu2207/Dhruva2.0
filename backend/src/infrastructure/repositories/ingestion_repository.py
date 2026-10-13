"""Dhruva.AI V2 — Ingestion & Provenance Repository.

Persistence layer for Data Sources, Import Batches, Staged Records,
Validation Results, Approvals, and Provenance Chains with strict tenant scoping.
"""

import uuid
from typing import Any, Dict, List, Optional
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.ingestion.models import (
    Approval,
    DataSource,
    ImportBatch,
    ProvenanceRecord,
    StagedRecord,
    ValidationResult,
)


class IngestionRepository:
    """Async repository governing the 9-stage data ingestion pipeline."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ---------------- Data Sources ----------------
    async def create_data_source(self, data_source: DataSource) -> DataSource:
        self.session.add(data_source)
        await self.session.flush()
        return data_source

    async def list_data_sources(self, institution_id: uuid.UUID) -> List[DataSource]:
        stmt = (
            select(DataSource)
            .where(DataSource.institution_id == institution_id)
            .order_by(desc(DataSource.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_data_source_by_id(
        self, institution_id: uuid.UUID, source_id: uuid.UUID
    ) -> Optional[DataSource]:
        stmt = select(DataSource).where(
            DataSource.id == source_id,
            DataSource.institution_id == institution_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ---------------- Import Batches ----------------
    async def create_import_batch(self, batch: ImportBatch) -> ImportBatch:
        self.session.add(batch)
        await self.session.flush()
        return batch

    async def list_import_batches(
        self,
        institution_id: uuid.UUID,
        status: Optional[str] = None,
        target_domain: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[ImportBatch]:
        stmt = select(ImportBatch).where(ImportBatch.institution_id == institution_id)
        if status:
            stmt = stmt.where(ImportBatch.status == status)
        if target_domain:
            stmt = stmt.where(ImportBatch.target_domain == target_domain)
        stmt = stmt.order_by(desc(ImportBatch.created_at)).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_import_batches(
        self, institution_id: uuid.UUID, status: Optional[str] = None
    ) -> int:
        stmt = select(func.count(ImportBatch.id)).where(ImportBatch.institution_id == institution_id)
        if status:
            stmt = stmt.where(ImportBatch.status == status)
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def get_import_batch_by_id(
        self, institution_id: uuid.UUID, batch_id: uuid.UUID
    ) -> Optional[ImportBatch]:
        stmt = select(ImportBatch).where(
            ImportBatch.id == batch_id,
            ImportBatch.institution_id == institution_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_import_batch_by_number(
        self, batch_number: str
    ) -> Optional[ImportBatch]:
        stmt = select(ImportBatch).where(ImportBatch.batch_number == batch_number)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ---------------- Staged Records ----------------
    async def create_staged_records(self, records: List[StagedRecord]) -> List[StagedRecord]:
        self.session.add_all(records)
        await self.session.flush()
        return records

    async def list_staged_records(
        self,
        institution_id: uuid.UUID,
        batch_id: uuid.UUID,
        stage_status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StagedRecord]:
        stmt = select(StagedRecord).where(
            StagedRecord.institution_id == institution_id,
            StagedRecord.import_batch_id == batch_id,
        )
        if stage_status:
            stmt = stmt.where(StagedRecord.stage_status == stage_status)
        stmt = stmt.order_by(StagedRecord.row_index).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_staged_record_by_id(
        self, institution_id: uuid.UUID, record_id: uuid.UUID
    ) -> Optional[StagedRecord]:
        stmt = select(StagedRecord).where(
            StagedRecord.id == record_id,
            StagedRecord.institution_id == institution_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ---------------- Validation Results ----------------
    async def create_validation_results(
        self, results: List[ValidationResult]
    ) -> List[ValidationResult]:
        self.session.add_all(results)
        await self.session.flush()
        return results

    async def list_validation_results_for_batch(
        self, institution_id: uuid.UUID, batch_id: uuid.UUID
    ) -> List[ValidationResult]:
        stmt = (
            select(ValidationResult)
            .join(StagedRecord, StagedRecord.id == ValidationResult.staged_record_id)
            .where(
                ValidationResult.institution_id == institution_id,
                StagedRecord.import_batch_id == batch_id,
            )
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ---------------- Approvals ----------------
    async def create_approval(self, approval: Approval) -> Approval:
        self.session.add(approval)
        await self.session.flush()
        return approval

    async def list_approvals_for_batch(
        self, institution_id: uuid.UUID, batch_id: uuid.UUID
    ) -> List[Approval]:
        stmt = select(Approval).where(
            Approval.institution_id == institution_id,
            Approval.import_batch_id == batch_id,
        ).order_by(desc(Approval.decided_at))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    # ---------------- Provenance Records ----------------
    async def create_provenance_records(
        self, records: List[ProvenanceRecord]
    ) -> List[ProvenanceRecord]:
        self.session.add_all(records)
        await self.session.flush()
        return records

    async def list_provenance_for_record(
        self, institution_id: uuid.UUID, authoritative_table: str, authoritative_record_id: uuid.UUID
    ) -> List[ProvenanceRecord]:
        stmt = select(ProvenanceRecord).where(
            ProvenanceRecord.institution_id == institution_id,
            ProvenanceRecord.authoritative_table == authoritative_table,
            ProvenanceRecord.authoritative_record_id == authoritative_record_id,
        ).order_by(desc(ProvenanceRecord.published_at))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_provenance_by_id(
        self, institution_id: uuid.UUID, provenance_id: uuid.UUID
    ) -> Optional[ProvenanceRecord]:
        stmt = select(ProvenanceRecord).where(
            ProvenanceRecord.id == provenance_id,
            ProvenanceRecord.institution_id == institution_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ---------------- Data Center Telemetry ----------------
    async def get_telemetry_metrics(self, institution_id: uuid.UUID) -> Dict[str, Any]:
        """Aggregate Data Center telemetry: total batches, records staged, published, error rates."""
        # Total batches
        total_batches_q = await self.session.execute(
            select(func.count(ImportBatch.id)).where(ImportBatch.institution_id == institution_id)
        )
        total_batches = total_batches_q.scalar_one() or 0

        # Batches pending review or approval
        pending_approval_q = await self.session.execute(
            select(func.count(ImportBatch.id)).where(
                ImportBatch.institution_id == institution_id,
                ImportBatch.status.in_(["VALIDATED", "STAGED", "IN_REVIEW"]),
            )
        )
        pending_approval = pending_approval_q.scalar_one() or 0

        # Batches published
        published_batches_q = await self.session.execute(
            select(func.count(ImportBatch.id)).where(
                ImportBatch.institution_id == institution_id,
                ImportBatch.status == "PUBLISHED",
            )
        )
        published_batches = published_batches_q.scalar_one() or 0

        # Aggregate record counts across all batches
        records_agg_q = await self.session.execute(
            select(
                func.coalesce(func.sum(ImportBatch.total_records), 0),
                func.coalesce(func.sum(ImportBatch.valid_records), 0),
                func.coalesce(func.sum(ImportBatch.warning_records), 0),
                func.coalesce(func.sum(ImportBatch.error_records), 0),
            ).where(ImportBatch.institution_id == institution_id)
        )
        rec_row = records_agg_q.one()
        total_records = int(rec_row[0])
        valid_records = int(rec_row[1])
        warning_records = int(rec_row[2])
        error_records = int(rec_row[3])

        # Active Data Sources
        active_sources_q = await self.session.execute(
            select(func.count(DataSource.id)).where(
                DataSource.institution_id == institution_id,
                DataSource.status == "ACTIVE",
            )
        )
        active_sources = active_sources_q.scalar_one() or 0

        # Total Provenance Records
        total_provenance_q = await self.session.execute(
            select(func.count(ProvenanceRecord.id)).where(
                ProvenanceRecord.institution_id == institution_id
            )
        )
        total_provenance = total_provenance_q.scalar_one() or 0

        failure_rate = (
            round((error_records / total_records) * 100, 2)
            if total_records > 0
            else 0.0
        )

        return {
            "total_batches": total_batches,
            "pending_approval": pending_approval,
            "published_batches": published_batches,
            "total_records": total_records,
            "valid_records": valid_records,
            "warning_records": warning_records,
            "error_records": error_records,
            "failure_rate_percent": failure_rate,
            "active_data_sources": active_sources,
            "total_provenance_records": total_provenance,
        }
