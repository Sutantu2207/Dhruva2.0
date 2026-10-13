"""Dhruva.AI V2 — Ingestion Pipeline, Data Center & Provenance API Endpoints.

Prefix: /institutions/{institution_slug}/...
Exposes the 9-stage data ingestion lifecycle, Review Queue, Approvals, Publication, and Provenance.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.ingestion.ingestion_service import IngestionService
from src.domain.identity.models import Institution, User
from src.domain.identity.roles import SystemRole
from src.infrastructure.persistence.postgres.database import get_db_session
from src.interfaces.http.dependencies import (
    build_response,
    get_current_tenant,
    get_current_user,
    require_roles,
)
from src.interfaces.http.schemas.envelope import ApiResponse, PaginationMeta
from src.interfaces.http.schemas.ingestion import (
    ApprovalRequest,
    ApprovalResponse,
    DataCenterTelemetryResponse,
    DataSourceCreateRequest,
    DataSourceResponse,
    ImportBatchResponse,
    ProvenanceRecordResponse,
    StagedRecordResponse,
)


router = APIRouter(prefix="/institutions/{institution_slug}", tags=["Data Center & Ingestion Pipeline"])


# =========================================================================
# DATA SOURCES
# =========================================================================
@router.get(
    "/data-center/sources",
    response_model=ApiResponse[List[DataSourceResponse]],
    summary="List Institutional Data Sources",
)
async def list_data_sources(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[DataSourceResponse]]:
    service = IngestionService(session)
    sources = await service.list_data_sources(tenant.id)
    data = [DataSourceResponse.model_validate(s) for s in sources]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/data-center/sources",
    response_model=ApiResponse[DataSourceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Institutional Data Source",
)
async def register_data_source(
    payload: DataSourceCreateRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[DataSourceResponse]:
    service = IngestionService(session)
    source = await service.create_data_source(
        institution_id=tenant.id,
        name=payload.name,
        source_type=payload.source_type,
        connection_details=payload.connection_details,
        actor_user_id=user.id,
    )
    return build_response(data=DataSourceResponse.model_validate(source), request=request)


# =========================================================================
# TELEMETRY OVERVIEW
# =========================================================================
@router.get(
    "/data-center/overview",
    response_model=ApiResponse[DataCenterTelemetryResponse],
    summary="Get Data Center Telemetry Overview",
)
async def get_data_center_overview(
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[DataCenterTelemetryResponse]:
    service = IngestionService(session)
    telemetry = await service.get_telemetry_overview(tenant.id)
    return build_response(data=DataCenterTelemetryResponse(**telemetry), request=request)


# =========================================================================
# INGESTION BATCH LIFECYCLE
# =========================================================================
@router.post(
    "/ingestion/upload",
    response_model=ApiResponse[ImportBatchResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload and Stage Document/Spreadsheet Batch",
)
async def upload_ingestion_file(
    request: Request,
    file: UploadFile = File(...),
    target_domain: str = Form(default="STUDENTS"),
    data_source_id: Optional[uuid.UUID] = Form(default=None),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ImportBatchResponse]:
    file_bytes = await file.read()
    service = IngestionService(session)
    batch = await service.upload_and_stage_file(
        institution_id=tenant.id,
        file_bytes=file_bytes,
        filename=file.filename or "uploaded_data.csv",
        mime_type=file.content_type or "text/csv",
        target_domain=target_domain,
        uploader_user_id=user.id,
        data_source_id=data_source_id,
    )
    return build_response(data=ImportBatchResponse.model_validate(batch), request=request)


@router.get(
    "/ingestion/batches",
    response_model=ApiResponse[List[ImportBatchResponse]],
    summary="List Import Batches",
)
async def list_import_batches(
    request: Request,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    target_domain: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[ImportBatchResponse]]:
    service = IngestionService(session)
    offset = (page - 1) * page_size
    batches = await service.repo.list_import_batches(
        institution_id=tenant.id,
        status=status_filter,
        target_domain=target_domain,
        limit=page_size,
        offset=offset,
    )
    total_records = await service.repo.count_import_batches(tenant.id, status=status_filter)
    data = [ImportBatchResponse.model_validate(b) for b in batches]
    pagination = PaginationMeta(page=page, page_size=page_size, total_records=total_records)
    return build_response(data=data, request=request, pagination=pagination)


@router.get(
    "/ingestion/batches/{batch_id}",
    response_model=ApiResponse[ImportBatchResponse],
    summary="Get Import Batch Details",
)
async def get_import_batch(
    batch_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ImportBatchResponse]:
    service = IngestionService(session)
    batch = await service.repo.get_import_batch_by_id(tenant.id, batch_id)
    if not batch:
        from src.core.errors import NotFoundError
        raise NotFoundError(f"Import batch {batch_id} not found.")
    return build_response(data=ImportBatchResponse.model_validate(batch), request=request)


@router.get(
    "/ingestion/batches/{batch_id}/staged-records",
    response_model=ApiResponse[List[StagedRecordResponse]],
    summary="List Staged Records for Review Queue",
)
async def list_staged_records(
    batch_id: uuid.UUID,
    request: Request,
    stage_status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=500),
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[StagedRecordResponse]]:
    service = IngestionService(session)
    offset = (page - 1) * page_size
    records = await service.repo.list_staged_records(
        institution_id=tenant.id,
        batch_id=batch_id,
        stage_status=stage_status,
        limit=page_size,
        offset=offset,
    )
    data = [StagedRecordResponse.model_validate(r) for r in records]
    pagination = PaginationMeta(page=page, page_size=page_size, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)


@router.post(
    "/ingestion/batches/{batch_id}/approve",
    response_model=ApiResponse[ApprovalResponse],
    summary="Submit Human Review & Approval for Batch",
)
async def approve_import_batch(
    batch_id: uuid.UUID,
    payload: ApprovalRequest,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN, SystemRole.HOD)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ApprovalResponse]:
    service = IngestionService(session)
    approval = await service.approve_or_reject_batch(
        institution_id=tenant.id,
        batch_id=batch_id,
        reviewer_user=user,
        decision=payload.decision,
        digital_signature=payload.digital_signature,
        notes=payload.notes or "",
    )
    return build_response(data=ApprovalResponse.model_validate(approval), request=request)


@router.post(
    "/ingestion/batches/{batch_id}/publish",
    response_model=ApiResponse[dict],
    summary="Publish Approved Batch into Authoritative Tables",
)
async def publish_import_batch(
    batch_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[dict]:
    service = IngestionService(session)
    result = await service.publish_batch(
        institution_id=tenant.id,
        batch_id=batch_id,
        publisher_user=user,
    )
    return build_response(data=result, request=request)


@router.post(
    "/ingestion/batches/{batch_id}/rollback",
    response_model=ApiResponse[ImportBatchResponse],
    summary="Rollback Batch",
)
async def rollback_import_batch(
    batch_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(require_roles(SystemRole.SUPER_ADMIN, SystemRole.INSTITUTION_ADMIN)),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[ImportBatchResponse]:
    service = IngestionService(session)
    batch = await service.rollback_batch(
        institution_id=tenant.id,
        batch_id=batch_id,
        actor_user=user,
    )
    return build_response(data=ImportBatchResponse.model_validate(batch), request=request)


# =========================================================================
# PROVENANCE TRACE
# =========================================================================
@router.get(
    "/ingestion/provenance/{authoritative_table}/{record_id}",
    response_model=ApiResponse[List[ProvenanceRecordResponse]],
    summary="Trace Immutable Provenance for Authoritative Record",
)
async def get_record_provenance(
    authoritative_table: str,
    record_id: uuid.UUID,
    request: Request,
    tenant: Institution = Depends(get_current_tenant),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse[List[ProvenanceRecordResponse]]:
    service = IngestionService(session)
    records = await service.get_provenance_trace(
        institution_id=tenant.id,
        authoritative_table=authoritative_table,
        record_id=record_id,
    )
    data = [ProvenanceRecordResponse.model_validate(p) for p in records]
    pagination = PaginationMeta(page=1, page_size=len(data) or 50, total_records=len(data))
    return build_response(data=data, request=request, pagination=pagination)
