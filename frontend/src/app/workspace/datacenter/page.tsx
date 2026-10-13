'use client';

/**
 * Dhruva.AI V2 — Institutional Data Center & Provenance Explorer Workspace
 *
 * Adheres strictly to the permanent platform rule: "NO SOURCE → NO DATA".
 * Integrates directly with:
 * - /institutions/{tenant}/data-center/overview
 * - /institutions/{tenant}/data-center/sources
 * - /institutions/{tenant}/ingestion/upload
 * - /institutions/{tenant}/ingestion/batches
 * - /institutions/{tenant}/ingestion/batches/{batch_id}/staged-records
 * - /institutions/{tenant}/ingestion/batches/{batch_id}/approve
 * - /institutions/{tenant}/ingestion/batches/{batch_id}/publish
 * - /institutions/{tenant}/ingestion/batches/{batch_id}/rollback
 * - /institutions/{tenant}/ingestion/provenance/{table}/{record_id}
 */

import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { useAuth } from '@/lib/auth/AuthContext';
import { api, ApiError } from '@/lib/api/client';
import {
  DataSource,
  DataSourceCreateInput,
  ImportBatch,
  StagedRecord,
  ProvenanceRecord,
  DataCenterTelemetry,
  TargetDomain,
  BatchStatus,
  StageStatus,
} from '@/types/datacenter';
import { PageHeader } from '@/components/ui/PageHeader';
import { Breadcrumbs } from '@/components/ui/Breadcrumbs';
import { Tabs } from '@/components/ui/Tabs';
import { Button } from '@/components/ui/Button';
import { Table, Column } from '@/components/ui/Table';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorState } from '@/components/ui/ErrorState';
import { Dialog } from '@/components/ui/Dialog';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Alert } from '@/components/ui/Alert';

// Server-enforced constants
const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50MB
const ALLOWED_MIME_EXTENSIONS = ['.csv', '.tsv', '.txt'];

export default function DataCenterPage() {
  const { user } = useAuth();
  const tenantSlug = user?.institution_slug || '';

  // Role permissions
  const canUpload = useMemo(() => {
    if (!user) return false;
    return user.roles.some((r) => ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD'].includes(r));
  }, [user]);

  const canApprove = useMemo(() => {
    if (!user) return false;
    return user.roles.some((r) => ['SUPER_ADMIN', 'INSTITUTION_ADMIN', 'HOD'].includes(r));
  }, [user]);

  const canPublishOrRollback = useMemo(() => {
    if (!user) return false;
    return user.roles.some((r) => ['SUPER_ADMIN', 'INSTITUTION_ADMIN'].includes(r));
  }, [user]);

  // Tab navigation
  const [activeTab, setActiveTab] = useState<'batches' | 'upload' | 'staging' | 'sources' | 'provenance'>('batches');

  // Telemetry Overview
  const [telemetry, setTelemetry] = useState<DataCenterTelemetry | null>(null);
  const [isTelemetryLoading, setIsTelemetryLoading] = useState<boolean>(true);

  // Batches
  const [batches, setBatches] = useState<ImportBatch[]>([]);
  const [batchStatusFilter, setBatchStatusFilter] = useState<string>('');
  const [batchDomainFilter, setBatchDomainFilter] = useState<string>('');
  const [isBatchesLoading, setIsBatchesLoading] = useState<boolean>(true);

  // Selected Batch for Staging / Inspection
  const [selectedBatchId, setSelectedBatchId] = useState<string>('');
  const [selectedBatch, setSelectedBatch] = useState<ImportBatch | null>(null);

  // Staged Records
  const [stagedRecords, setStagedRecords] = useState<StagedRecord[]>([]);
  const [stageStatusFilter, setStageStatusFilter] = useState<string>('');
  const [isStagedLoading, setIsStagedLoading] = useState<boolean>(false);
  const [inspectingRecord, setInspectingRecord] = useState<StagedRecord | null>(null);

  // Data Sources
  const [sources, setSources] = useState<DataSource[]>([]);
  const [isSourcesLoading, setIsSourcesLoading] = useState<boolean>(false);

  // Provenance Explorer lookup
  const [provTable, setProvTable] = useState<string>('students');
  const [provRecordId, setProvRecordId] = useState<string>('');
  const [provResults, setProvResults] = useState<ProvenanceRecord[]>([]);
  const [isProvLoading, setIsProvLoading] = useState<boolean>(false);
  const [provSearched, setProvSearched] = useState<boolean>(false);

  // Global Page Error
  const [error, setError] = useState<{ message: string; code?: string; requestId?: string } | null>(null);

  // Action Success Toast / Banner
  const [actionNotice, setActionNotice] = useState<{ type: 'success' | 'warning' | 'error'; message: string } | null>(null);

  // Dialog Modals
  const [approvalModalBatch, setApprovalModalBatch] = useState<ImportBatch | null>(null);
  const [approvalDecision, setApprovalDecision] = useState<'APPROVED' | 'REJECTED'>('APPROVED');
  const [approvalSignature, setApprovalSignature] = useState<string>('');
  const [approvalNotes, setApprovalNotes] = useState<string>('');
  const [isSubmittingApproval, setIsSubmittingApproval] = useState<boolean>(false);

  // Create Data Source Modal
  const [isCreateSourceOpen, setIsCreateSourceOpen] = useState<boolean>(false);
  const [sourceName, setSourceName] = useState<string>('');
  const [sourceType, setSourceType] = useState<string>('CSV_UPLOAD');
  const [sourceConnectionDetails, setSourceConnectionDetails] = useState<string>('{}');
  const [isCreatingSource, setIsCreatingSource] = useState<boolean>(false);

  // Upload Form State
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDomain, setUploadDomain] = useState<TargetDomain>('STUDENTS');
  const [uploadSourceId, setUploadSourceId] = useState<string>('');
  const [uploadFileSha256, setUploadFileSha256] = useState<string>('');
  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadFeedback, setUploadFeedback] = useState<ImportBatch | null>(null);

  // ---------------------------------------------------------------------------
  // 1. DATA LOADERS
  // ---------------------------------------------------------------------------
  const loadTelemetry = useCallback(async () => {
    if (!tenantSlug) return;
    setIsTelemetryLoading(true);
    try {
      const data = await api.get<DataCenterTelemetry>(`/institutions/${tenantSlug}/data-center/overview`);
      setTelemetry(data);
    } catch {
      // Telemetry might be 403 for non-privileged roles, handled gracefully
    } finally {
      setIsTelemetryLoading(false);
    }
  }, [tenantSlug]);

  const loadBatches = useCallback(async () => {
    if (!tenantSlug) return;
    setIsBatchesLoading(true);
    setError(null);
    try {
      let query = `?page=1&page_size=50`;
      if (batchStatusFilter) query += `&status=${encodeURIComponent(batchStatusFilter)}`;
      if (batchDomainFilter) query += `&target_domain=${encodeURIComponent(batchDomainFilter)}`;

      const data = await api.get<ImportBatch[]>(`/institutions/${tenantSlug}/ingestion/batches${query}`);
      setBatches(data);

      // If no batch is selected, auto-select the latest
      if (data.length > 0 && !selectedBatchId) {
        setSelectedBatchId(data[0].id);
        setSelectedBatch(data[0]);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      } else {
        setError({ message: 'Failed to load ingestion batches.' });
      }
    } finally {
      setIsBatchesLoading(false);
    }
  }, [tenantSlug, batchStatusFilter, batchDomainFilter, selectedBatchId]);

  const loadSources = useCallback(async () => {
    if (!tenantSlug) return;
    setIsSourcesLoading(true);
    try {
      const data = await api.get<DataSource[]>(`/institutions/${tenantSlug}/data-center/sources`);
      setSources(data);
    } catch {
      // Handled gracefully
    } finally {
      setIsSourcesLoading(false);
    }
  }, [tenantSlug]);

  const loadStagedRecords = useCallback(async (batchId: string) => {
    if (!tenantSlug || !batchId) return;
    setIsStagedLoading(true);
    setError(null);
    try {
      let query = `?page=1&page_size=100`;
      if (stageStatusFilter) query += `&stage_status=${encodeURIComponent(stageStatusFilter)}`;

      const data = await api.get<StagedRecord[]>(
        `/institutions/${tenantSlug}/ingestion/batches/${batchId}/staged-records${query}`
      );
      setStagedRecords(data);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      } else {
        setError({ message: 'Failed to retrieve staged records.' });
      }
    } finally {
      setIsStagedLoading(false);
    }
  }, [tenantSlug, stageStatusFilter]);

  // Initial load
  useEffect(() => {
    if (tenantSlug) {
      loadTelemetry();
      loadBatches();
      loadSources();
    }
  }, [tenantSlug, loadTelemetry, loadBatches, loadSources]);

  // Staged records reload when batch or stage filter changes
  useEffect(() => {
    if (selectedBatchId) {
      loadStagedRecords(selectedBatchId);
      const b = batches.find((item) => item.id === selectedBatchId);
      if (b) setSelectedBatch(b);
    }
  }, [selectedBatchId, stageStatusFilter, loadStagedRecords, batches]);

  // Compute SHA-256 for selected file
  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) {
      setUploadFile(null);
      setUploadFileSha256('');
      return;
    }

    // Check size limit
    if (file.size > MAX_FILE_SIZE_BYTES) {
      setError({
        message: `File size exceeds the server-enforced limit of 50 MB (selected: ${(file.size / (1024 * 1024)).toFixed(1)} MB).`,
      });
      setUploadFile(null);
      setUploadFileSha256('');
      return;
    }

    // Check format
    const lowerName = file.name.toLowerCase();
    const hasValidExt = ALLOWED_MIME_EXTENSIONS.some((ext) => lowerName.endsWith(ext));
    if (!hasValidExt) {
      setError({
        message: `File format not supported. Only CSV and delimited text files (.csv, .tsv, .txt) are accepted by the server.`,
      });
      setUploadFile(null);
      setUploadFileSha256('');
      return;
    }

    setError(null);
    setUploadFile(file);

    // Compute checksum locally for instant audit transparency
    try {
      const buffer = await file.arrayBuffer();
      const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
      setUploadFileSha256(hashHex);
    } catch {
      setUploadFileSha256('Checksum calculation pending server verification');
    }
  };

  // ---------------------------------------------------------------------------
  // 2. UPLOAD ACTION
  // ---------------------------------------------------------------------------
  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile || !tenantSlug) return;

    setIsUploading(true);
    setError(null);
    setUploadFeedback(null);
    setActionNotice(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('target_domain', uploadDomain);
      if (uploadSourceId) {
        formData.append('data_source_id', uploadSourceId);
      }

      const responseBatch = await api.upload<ImportBatch>(
        `/institutions/${tenantSlug}/ingestion/upload`,
        formData
      );

      setUploadFeedback(responseBatch);
      setActionNotice({
        type: 'success',
        message: `Batch ${responseBatch.batch_number} staged successfully with ${responseBatch.total_records} records (${responseBatch.valid_records} valid, ${responseBatch.error_records} errors).`,
      });

      // Reset file input
      setUploadFile(null);
      setUploadFileSha256('');

      // Refresh batches & telemetry
      await loadBatches();
      await loadTelemetry();

      // Set active batch to newly uploaded
      setSelectedBatchId(responseBatch.id);
      setSelectedBatch(responseBatch);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      } else {
        setError({ message: 'File upload and staging failed. Please verify network and server state.' });
      }
    } finally {
      setIsUploading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 3. APPROVAL / REJECTION ACTION
  // ---------------------------------------------------------------------------
  const handleApprovalSubmit = async () => {
    if (!approvalModalBatch || !tenantSlug) return;
    setIsSubmittingApproval(true);
    setError(null);

    try {
      const sig = approvalSignature.trim() || `Signed by ${user?.full_name || user?.email}`;
      await api.post(
        `/institutions/${tenantSlug}/ingestion/batches/${approvalModalBatch.id}/approve`,
        {
          decision: approvalDecision,
          digital_signature: sig,
          notes: approvalNotes.trim(),
        }
      );

      setActionNotice({
        type: approvalDecision === 'APPROVED' ? 'success' : 'warning',
        message: `Batch ${approvalModalBatch.batch_number} has been ${approvalDecision.toLowerCase()} by reviewer.`,
      });

      setApprovalModalBatch(null);
      setApprovalSignature('');
      setApprovalNotes('');

      await loadBatches();
      await loadTelemetry();
      if (selectedBatchId === approvalModalBatch.id) {
        await loadStagedRecords(selectedBatchId);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      } else {
        setError({ message: 'Failed to record batch decision.' });
      }
    } finally {
      setIsSubmittingApproval(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 4. PUBLISH BATCH ACTION
  // ---------------------------------------------------------------------------
  const handlePublishBatch = async (batch: ImportBatch) => {
    if (!tenantSlug) return;
    if (!confirm(`Are you sure you want to publish batch ${batch.batch_number} into live authoritative tables? This action will generate immutable provenance chains.`)) {
      return;
    }

    setError(null);
    try {
      const result = await api.post<{ published_records: number; provenance_records_created: number }>(
        `/institutions/${tenantSlug}/ingestion/batches/${batch.id}/publish`
      );

      setActionNotice({
        type: 'success',
        message: `Batch ${batch.batch_number} successfully published. ${result.published_records} authoritative records updated with ${result.provenance_records_created} provenance chains created.`,
      });

      await loadBatches();
      await loadTelemetry();
      if (selectedBatchId === batch.id) {
        await loadStagedRecords(selectedBatchId);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      } else {
        setError({ message: 'Failed to publish batch into authoritative tables.' });
      }
    }
  };

  // ---------------------------------------------------------------------------
  // 5. ROLLBACK BATCH ACTION
  // ---------------------------------------------------------------------------
  const handleRollbackBatch = async (batch: ImportBatch) => {
    if (!tenantSlug) return;
    if (!confirm(`WARNING: Are you sure you want to rollback batch ${batch.batch_number}? This marks staged records as ROLLED_BACK.`)) {
      return;
    }

    setError(null);
    try {
      await api.post(`/institutions/${tenantSlug}/ingestion/batches/${batch.id}/rollback`);
      setActionNotice({
        type: 'warning',
        message: `Batch ${batch.batch_number} has been rolled back.`,
      });

      await loadBatches();
      await loadTelemetry();
      if (selectedBatchId === batch.id) {
        await loadStagedRecords(selectedBatchId);
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      } else {
        setError({ message: 'Failed to rollback batch.' });
      }
    }
  };

  // ---------------------------------------------------------------------------
  // 6. CREATE DATA SOURCE
  // ---------------------------------------------------------------------------
  const handleCreateSource = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceName.trim() || !tenantSlug) return;

    setIsCreatingSource(true);
    setError(null);

    let parsedDetails: Record<string, unknown> = {};
    try {
      if (sourceConnectionDetails.trim()) {
        parsedDetails = JSON.parse(sourceConnectionDetails);
      }
    } catch {
      setError({ message: 'Connection details must be valid JSON object.' });
      setIsCreatingSource(false);
      return;
    }

    try {
      const payload: DataSourceCreateInput = {
        name: sourceName.trim(),
        source_type: sourceType,
        connection_details: parsedDetails,
      };

      await api.post(`/institutions/${tenantSlug}/data-center/sources`, payload);
      setActionNotice({
        type: 'success',
        message: `Data source '${sourceName}' registered in the institutional catalog.`,
      });

      setIsCreateSourceOpen(false);
      setSourceName('');
      setSourceConnectionDetails('{}');
      await loadSources();
      await loadTelemetry();
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      } else {
        setError({ message: 'Failed to register data source.' });
      }
    } finally {
      setIsCreatingSource(false);
    }
  };

  // ---------------------------------------------------------------------------
  // 7. PROVENANCE LOOKUP
  // ---------------------------------------------------------------------------
  const handleProvenanceSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!provRecordId.trim() || !tenantSlug) return;

    setIsProvLoading(true);
    setError(null);
    setProvSearched(true);
    setProvResults([]);

    try {
      const results = await api.get<ProvenanceRecord[]>(
        `/institutions/${tenantSlug}/ingestion/provenance/${provTable.toLowerCase().trim()}/${provRecordId.trim()}`
      );
      setProvResults(results);
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setError({ message: err.message, code: err.code, requestId: err.requestId });
      } else {
        setError({ message: 'Failed to retrieve provenance trace for record.' });
      }
    } finally {
      setIsProvLoading(false);
    }
  };

  // ---------------------------------------------------------------------------
  // RENDER HELPERS
  // ---------------------------------------------------------------------------
  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'PUBLISHED':
      case 'VALID':
      case 'APPROVED':
        return 'success';
      case 'STAGED':
      case 'ACTIVE':
        return 'info';
      case 'WARNING':
      case 'PENDING':
        return 'warning';
      case 'ERROR':
      case 'REJECTED':
      case 'ROLLED_BACK':
        return 'danger';
      default:
        return 'default';
    }
  };

  // Batches Table Columns
  // Batches Table Columns
  const batchColumns: Column<ImportBatch>[] = [
    {
      key: 'batch_number',
      header: 'Batch Number',
      render: (b) => (
        <div>
          <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{b.batch_number}</span>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{b.original_file_name}</div>
        </div>
      ),
    },
    {
      key: 'target_domain',
      header: 'Domain',
      render: (b) => <Badge variant="outline">{b.target_domain}</Badge>,
    },
    {
      key: 'records_breakdown',
      header: 'Records Breakdown',
      render: (b) => (
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', fontWeight: 600 }}>{b.total_records} total</span>
          <span style={{ fontSize: '11px', color: 'var(--status-success)' }}>{b.valid_records} valid</span>
          {b.warning_records > 0 && (
            <span style={{ fontSize: '11px', color: 'var(--status-warning)' }}>{b.warning_records} warn</span>
          )}
          {b.error_records > 0 && (
            <span style={{ fontSize: '11px', color: 'var(--status-danger)' }}>{b.error_records} err</span>
          )}
        </div>
      ),
    },
    {
      key: 'file_sha256',
      header: 'Checksum (SHA-256)',
      render: (b) => (
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '11px',
            color: 'var(--text-muted)',
          }}
          title={b.file_sha256}
        >
          {b.file_sha256 ? `${b.file_sha256.substring(0, 10)}...` : 'N/A'}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Lifecycle Status',
      render: (b) => <Badge variant={getStatusBadgeVariant(b.status)}>{b.status}</Badge>,
    },
    {
      key: 'created_at',
      header: 'Created At',
      render: (b) => (
        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
          {new Date(b.created_at).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (b) => (
        <div style={{ display: 'flex', gap: '6px' }}>
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setSelectedBatchId(b.id);
              setSelectedBatch(b);
              setActiveTab('staging');
            }}
          >
            Inspect
          </Button>

          {b.status === 'STAGED' && canApprove && (
            <Button
              size="sm"
              variant="primary"
              onClick={() => {
                setApprovalModalBatch(b);
                setApprovalDecision('APPROVED');
                setApprovalSignature(`Signed by ${user?.full_name || user?.email}`);
              }}
            >
              Review
            </Button>
          )}

          {b.status === 'APPROVED' && canPublishOrRollback && (
            <Button size="sm" variant="primary" onClick={() => handlePublishBatch(b)}>
              Publish
            </Button>
          )}

          {(b.status === 'PUBLISHED' || b.status === 'APPROVED') && canPublishOrRollback && (
            <Button size="sm" variant="danger" onClick={() => handleRollbackBatch(b)}>
              Rollback
            </Button>
          )}
        </div>
      ),
    },
  ];

  // Staged Records Table Columns
  const stagedColumns: Column<StagedRecord>[] = [
    {
      key: 'extraction_coordinate',
      header: 'Coordinate',
      render: (r) => (
        <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
          {r.extraction_coordinate || `Row ${r.row_index}`}
        </span>
      ),
    },
    {
      key: 'target_entity_type',
      header: 'Entity Type',
      render: (r) => <Badge variant="outline">{r.target_entity_type}</Badge>,
    },
    {
      key: 'stage_status',
      header: 'Status',
      render: (r) => <Badge variant={getStatusBadgeVariant(r.stage_status)}>{r.stage_status}</Badge>,
    },
    {
      key: 'validation_findings',
      header: 'Validation Findings',
      render: (r) => {
        if (!r.validation_results || r.validation_results.length === 0) {
          return <span style={{ fontSize: '12px', color: 'var(--status-success)' }}>✓ Passed all rules</span>;
        }
        return (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
            {r.validation_results.map((v, i) => (
              <span
                key={v.id || i}
                style={{
                  fontSize: '11px',
                  color: v.severity === 'ERROR' ? 'var(--status-danger)' : 'var(--status-warning)',
                }}
              >
                [{v.rule_code}] {v.field_name}: {v.message}
              </span>
            ))}
          </div>
        );
      },
    },
    {
      key: 'payload_preview',
      header: 'Payload Preview',
      render: (r) => (
        <span style={{ fontSize: '11px', color: 'var(--text-secondary)' }}>
          {Object.entries(r.normalized_payload || {})
            .slice(0, 3)
            .map(([k, v]) => `${k}=${v}`)
            .join(' | ')}
        </span>
      ),
    },
    {
      key: 'detail_actions',
      header: 'Detail',
      render: (r) => (
        <Button size="sm" variant="outline" onClick={() => setInspectingRecord(r)}>
          View Payloads
        </Button>
      ),
    },
  ];

  // Data Sources Table Columns
  const sourceColumns: Column<DataSource>[] = [
    {
      key: 'name',
      header: 'Source Name',
      render: (s) => <span style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{s.name}</span>,
    },
    {
      key: 'source_type',
      header: 'Type',
      render: (s) => <Badge variant="outline">{s.source_type}</Badge>,
    },
    {
      key: 'status',
      header: 'Status',
      render: (s) => <Badge variant={s.status === 'ACTIVE' ? 'success' : 'default'}>{s.status}</Badge>,
    },
    {
      key: 'created_at',
      header: 'Registered At',
      render: (s) => (
        <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
          {new Date(s.created_at).toLocaleDateString()}
        </span>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1400px', margin: '0 auto' }}>
      {/* Header */}
      <Breadcrumbs
        items={[
          { label: 'Workspace', href: '/workspace' },
          { label: 'Data Center & Ingestion' },
        ]}
      />
      <PageHeader
        title="Institutional Data Center"
        description="Unified staging pipeline, deterministic rule validation, human governance, and immutable provenance tracking."
        action={
          <div style={{ display: 'flex', gap: '8px' }}>
            {canUpload && (
              <Button variant="primary" onClick={() => setActiveTab('upload')}>
                Upload Batch
              </Button>
            )}
            {canPublishOrRollback && (
              <Button variant="outline" onClick={() => setIsCreateSourceOpen(true)}>
                + Register Data Source
              </Button>
            )}
          </div>
        }
      />

      {/* Principle Banner */}
      <div
        style={{
          marginTop: '16px',
          marginBottom: '20px',
          padding: '12px 16px',
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--bg-surface-elevated)',
          borderLeft: '4px solid var(--brand-primary)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
        }}
      >
        <div>
          <span style={{ fontWeight: 700, fontSize: '12px', letterSpacing: '0.05em', color: 'var(--brand-primary)' }}>
            PERMANENT PLATFORM PRINCIPLE: NO SOURCE → NO DATA
          </span>
          <p style={{ margin: '4px 0 0', fontSize: '12px', color: 'var(--text-secondary)' }}>
            Authoritative institutional records are never synthesized. Raw ingestions remain quarantined in staging
            until validated against deterministic rules, formally reviewed, and signed off.
          </p>
        </div>
        <Badge variant="outline" size="sm">
          9-Stage Pipeline Active
        </Badge>
      </div>

      {/* Global Alerts / Notices */}
      {actionNotice && (
        <div style={{ marginBottom: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ flex: 1 }}>
            <Alert
              variant={actionNotice.type === 'error' ? 'danger' : actionNotice.type}
              title={actionNotice.type === 'success' ? 'Operation Completed' : 'Audit Notice'}
            >
              {actionNotice.message}
            </Alert>
          </div>
          <Button size="sm" variant="ghost" onClick={() => setActionNotice(null)} style={{ marginLeft: '8px' }}>
            Dismiss
          </Button>
        </div>
      )}

      {error && (
        <div style={{ marginBottom: '16px' }}>
          <ErrorState
            title="System Alert"
            message={error.message}
            code={error.code}
            requestId={error.requestId}
            onRetry={() => {
              setError(null);
              loadBatches();
              loadTelemetry();
            }}
          />
        </div>
      )}

      {/* Telemetry Metrics Bar */}
      {telemetry && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '12px',
            marginBottom: '24px',
          }}
        >
          <div style={{ padding: '16px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>TOTAL BATCHES</div>
            <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
              {telemetry.total_batches}
            </div>
          </div>
          <div style={{ padding: '16px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>PENDING APPROVAL</div>
            <div style={{ fontSize: '22px', fontWeight: 700, color: telemetry.pending_approval > 0 ? 'var(--status-warning)' : 'var(--text-primary)', marginTop: '4px' }}>
              {telemetry.pending_approval}
            </div>
          </div>
          <div style={{ padding: '16px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>PUBLISHED TO LIVE</div>
            <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--status-success)', marginTop: '4px' }}>
              {telemetry.published_batches}
            </div>
          </div>
          <div style={{ padding: '16px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>STAGED RECORDS</div>
            <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--text-primary)', marginTop: '4px' }}>
              {telemetry.total_records}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
              {telemetry.valid_records} valid | {telemetry.error_records} errors
            </div>
          </div>
          <div style={{ padding: '16px', backgroundColor: 'var(--bg-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>PROVENANCE CHAINS</div>
            <div style={{ fontSize: '22px', fontWeight: 700, color: 'var(--brand-primary)', marginTop: '4px' }}>
              {telemetry.total_provenance_records}
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <Tabs
        tabs={[
          { id: 'batches', label: `Ingestion Batches (${batches.length})` },
          { id: 'staging', label: selectedBatch ? `Staged Records [${selectedBatch.batch_number}]` : 'Staged Records' },
          { id: 'upload', label: 'Upload & Stage' },
          { id: 'sources', label: `Data Sources (${sources.length})` },
          { id: 'provenance', label: 'Provenance Explorer' },
        ]}
        activeTab={activeTab}
        onChange={(tabId) => setActiveTab(tabId as any)}
      />

      <div style={{ marginTop: '20px' }}>
        {/* ================================================================= */}
        {/* TAB 1: BATCHES */}
        {/* ================================================================= */}
        {activeTab === 'batches' && (
          <div>
            {/* Filter toolbar */}
            <div
              style={{
                display: 'flex',
                gap: '12px',
                marginBottom: '16px',
                alignItems: 'center',
                flexWrap: 'wrap',
              }}
            >
              <div style={{ width: '200px' }}>
                <Select
                  value={batchStatusFilter}
                  onChange={(e) => setBatchStatusFilter(e.target.value)}
                  options={[
                    { value: '', label: 'All Lifecycle Statuses' },
                    { value: 'STAGED', label: 'STAGED (Pending Review)' },
                    { value: 'APPROVED', label: 'APPROVED (Awaiting Publish)' },
                    { value: 'PUBLISHED', label: 'PUBLISHED (Live)' },
                    { value: 'REJECTED', label: 'REJECTED' },
                    { value: 'ROLLED_BACK', label: 'ROLLED_BACK' },
                  ]}
                />
              </div>

              <div style={{ width: '180px' }}>
                <Select
                  value={batchDomainFilter}
                  onChange={(e) => setBatchDomainFilter(e.target.value)}
                  options={[
                    { value: '', label: 'All Target Domains' },
                    { value: 'STUDENTS', label: 'Students' },
                    { value: 'COURSES', label: 'Courses' },
                    { value: 'FACULTY', label: 'Faculty' },
                  ]}
                />
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setBatchStatusFilter('');
                  setBatchDomainFilter('');
                }}
              >
                Reset Filters
              </Button>
            </div>

            {isBatchesLoading ? (
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                Loading ingestion batches...
              </div>
            ) : batches.length === 0 ? (
              <EmptyState
                title="No Ingestion Batches Found"
                description={
                  batchStatusFilter || batchDomainFilter
                    ? 'No batches match the applied filter criteria.'
                    : 'No data documents have been staged yet. Upload a CSV file to initiate the ingestion lifecycle.'
                }
                actionLabel={canUpload ? 'Upload First Batch' : undefined}
                onAction={canUpload ? () => setActiveTab('upload') : undefined}
              />
            ) : (
              <Table
                columns={batchColumns}
                data={batches}
                keyExtractor={(b) => b.id}
              />
            )}
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 2: STAGING REVIEW QUEUE */}
        {/* ================================================================= */}
        {activeTab === 'staging' && (
          <div>
            {batches.length === 0 ? (
              <EmptyState
                title="No Batches Available"
                description="Upload an ingestion batch to inspect quarantined rows and deterministic validation rules."
                actionLabel={canUpload ? 'Upload Batch' : undefined}
                onAction={canUpload ? () => setActiveTab('upload') : undefined}
              />
            ) : (
              <div>
                {/* Batch Selector Header */}
                <div
                  style={{
                    padding: '16px',
                    backgroundColor: 'var(--bg-surface)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                    marginBottom: '16px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    flexWrap: 'wrap',
                    gap: '12px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '280px' }}>
                      <Select
                        label="Select Batch to Inspect"
                        value={selectedBatchId}
                        onChange={(e) => {
                          setSelectedBatchId(e.target.value);
                          const b = batches.find((item) => item.id === e.target.value);
                          if (b) setSelectedBatch(b);
                        }}
                        options={batches.map((b) => ({
                          value: b.id,
                          label: `${b.batch_number} (${b.target_domain} - ${b.status})`,
                        }))}
                      />
                    </div>

                    <div style={{ width: '180px', marginTop: '18px' }}>
                      <Select
                        value={stageStatusFilter}
                        onChange={(e) => setStageStatusFilter(e.target.value)}
                        options={[
                          { value: '', label: 'All Row Statuses' },
                          { value: 'VALID', label: 'VALID Only' },
                          { value: 'WARNING', label: 'WARNING Only' },
                          { value: 'ERROR', label: 'ERROR Only' },
                          { value: 'APPROVED', label: 'APPROVED Only' },
                        ]}
                      />
                    </div>
                  </div>

                  {selectedBatch && (
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <Badge variant={getStatusBadgeVariant(selectedBatch.status)} size="md">
                        {selectedBatch.status}
                      </Badge>

                      {selectedBatch.status === 'STAGED' && canApprove && (
                        <Button
                          size="sm"
                          variant="primary"
                          onClick={() => {
                            setApprovalModalBatch(selectedBatch);
                            setApprovalDecision('APPROVED');
                            setApprovalSignature(`Signed by ${user?.full_name || user?.email}`);
                          }}
                        >
                          Review & Sign
                        </Button>
                      )}

                      {selectedBatch.status === 'APPROVED' && canPublishOrRollback && (
                        <Button size="sm" variant="primary" onClick={() => handlePublishBatch(selectedBatch)}>
                          Publish Live
                        </Button>
                      )}
                    </div>
                  )}
                </div>

                {/* Staged Table */}
                {isStagedLoading ? (
                  <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    Loading quarantined rows and validation rules...
                  </div>
                ) : stagedRecords.length === 0 ? (
                  <EmptyState
                    title="No Staged Rows Found"
                    description={
                      stageStatusFilter
                        ? `No rows in batch ${selectedBatch?.batch_number} match filter '${stageStatusFilter}'.`
                        : `No staged records found in batch ${selectedBatch?.batch_number}.`
                    }
                  />
                ) : (
                  <Table
                    columns={stagedColumns}
                    data={stagedRecords}
                    keyExtractor={(r) => r.id}
                  />
                )}
              </div>
            )}
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 3: UPLOAD & INGEST */}
        {/* ================================================================= */}
        {activeTab === 'upload' && (
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div
              style={{
                backgroundColor: 'var(--bg-surface)',
                padding: '28px',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-subtle)',
              }}
            >
              <h3 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 8px', color: 'var(--text-primary)' }}>
                Ingest New Institutional Batch
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '0 0 20px', lineHeight: 1.5 }}>
                Documents uploaded here are parsed, normalized into canonical schemas, checked with deterministic
                validation rules, and held in an isolated quarantine table.
              </p>

              {/* Server Enforcement Notice */}
              <div
                style={{
                  padding: '12px',
                  borderRadius: 'var(--radius-md)',
                  backgroundColor: 'var(--bg-surface-elevated)',
                  marginBottom: '20px',
                  fontSize: '12px',
                  color: 'var(--text-secondary)',
                }}
              >
                <div>
                  <strong>Supported Document Formats:</strong> CSV and Delimited text files (.csv, .tsv, .txt)
                </div>
                <div>
                  <strong>Size Limit:</strong> 50 MB maximum (server-enforced)
                </div>
                <div>
                  <strong>Header Normalization:</strong> Case-insensitive synonyms mapped to canonical schemas
                  (e.g., student_email → email, reg_no → roll_number).
                </div>
              </div>

              <form onSubmit={handleUploadSubmit}>
                {/* Target Domain */}
                <div style={{ marginBottom: '16px' }}>
                  <Select
                    label="Target Academic Domain *"
                    value={uploadDomain}
                    onChange={(e) => setUploadDomain(e.target.value as TargetDomain)}
                    options={[
                      { value: 'STUDENTS', label: 'Students (Roster, Roll Numbers, Contact Details)' },
                      { value: 'COURSES', label: 'Courses (Codes, Titles, Credit Hours, Departments)' },
                      { value: 'FACULTY', label: 'Faculty (Instructors, Designations, Departments)' },
                    ]}
                  />
                </div>

                {/* Data Source Linkage */}
                <div style={{ marginBottom: '16px' }}>
                  <Select
                    label="Associated Data Source (Optional)"
                    value={uploadSourceId}
                    onChange={(e) => setUploadSourceId(e.target.value)}
                    options={[
                      { value: '', label: 'Ad-hoc Manual Ingestion' },
                      ...sources.map((s) => ({ value: s.id, label: `${s.name} (${s.source_type})` })),
                    ]}
                  />
                </div>

                {/* File Dropzone */}
                <div style={{ marginBottom: '20px' }}>
                  <label
                    style={{
                      display: 'block',
                      fontSize: '13px',
                      fontWeight: 600,
                      marginBottom: '6px',
                      color: 'var(--text-primary)',
                    }}
                  >
                    Select File (.csv, .tsv, .txt) *
                  </label>
                  <input
                    type="file"
                    accept=".csv,.tsv,.txt,text/csv,text/tab-separated-values,text/plain"
                    onChange={handleFileChange}
                    required
                    style={{
                      display: 'block',
                      width: '100%',
                      padding: '10px',
                      fontSize: '13px',
                      borderRadius: 'var(--radius-md)',
                      border: '1px dashed var(--border-strong)',
                      backgroundColor: 'var(--bg-surface-elevated)',
                      color: 'var(--text-primary)',
                      cursor: 'pointer',
                    }}
                  />

                  {uploadFile && (
                    <div
                      style={{
                        marginTop: '10px',
                        padding: '10px 14px',
                        borderRadius: 'var(--radius-md)',
                        backgroundColor: 'var(--bg-surface-subtle)',
                        fontSize: '12px',
                      }}
                    >
                      <div style={{ color: 'var(--text-primary)', fontWeight: 600 }}>
                        File: {uploadFile.name} ({(uploadFile.size / 1024).toFixed(1)} KB)
                      </div>
                      <div style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', fontSize: '11px', marginTop: '2px' }}>
                        SHA-256 Checksum: {uploadFileSha256}
                      </div>
                    </div>
                  )}
                </div>

                <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                  <Button
                    type="submit"
                    variant="primary"
                    disabled={!uploadFile || isUploading}
                  >
                    {isUploading ? 'Validating & Staging...' : 'Upload & Run Validations'}
                  </Button>
                </div>
              </form>

              {/* Upload Success Details */}
              {uploadFeedback && (
                <div
                  style={{
                    marginTop: '24px',
                    padding: '16px',
                    borderRadius: 'var(--radius-md)',
                    backgroundColor: 'var(--status-success-subtle)',
                    border: '1px solid var(--status-success)',
                  }}
                >
                  <div style={{ fontWeight: 700, color: 'var(--status-success)', fontSize: '14px' }}>
                    Batch Staged: {uploadFeedback.batch_number}
                  </div>
                  <div style={{ marginTop: '8px', fontSize: '12px', color: 'var(--text-primary)' }}>
                    Total Records: <strong>{uploadFeedback.total_records}</strong> | Valid:{' '}
                    <strong style={{ color: 'var(--status-success)' }}>{uploadFeedback.valid_records}</strong> | Errors:{' '}
                    <strong style={{ color: 'var(--status-danger)' }}>{uploadFeedback.error_records}</strong>
                  </div>
                  <div style={{ marginTop: '12px' }}>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        setSelectedBatchId(uploadFeedback.id);
                        setSelectedBatch(uploadFeedback);
                        setActiveTab('staging');
                      }}
                    >
                      Inspect Staged Records Now →
                    </Button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 4: DATA SOURCES REGISTRY */}
        {/* ================================================================= */}
        {activeTab === 'sources' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <h4 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: 'var(--text-primary)' }}>
                  Institutional Data Sources
                </h4>
                <p style={{ margin: '2px 0 0', fontSize: '12px', color: 'var(--text-muted)' }}>
                  Registered external feeds, ERP exports, and SIS endpoints.
                </p>
              </div>

              {canPublishOrRollback && (
                <Button size="sm" variant="primary" onClick={() => setIsCreateSourceOpen(true)}>
                  + Add Data Source
                </Button>
              )}
            </div>

            {isSourcesLoading ? (
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                Loading registered sources...
              </div>
            ) : sources.length === 0 ? (
              <EmptyState
                title="No Data Sources Configured"
                description="Register institutional sources (e.g. Registrar ERP, SIS Sync, CSV dropboxes) to track ingestions by origin."
                actionLabel={canPublishOrRollback ? 'Register First Data Source' : undefined}
                onAction={canPublishOrRollback ? () => setIsCreateSourceOpen(true) : undefined}
              />
            ) : (
              <Table
                columns={sourceColumns}
                data={sources}
                keyExtractor={(s) => s.id}
              />
            )}
          </div>
        )}

        {/* ================================================================= */}
        {/* TAB 5: PROVENANCE EXPLORER */}
        {/* ================================================================= */}
        {activeTab === 'provenance' && (
          <div style={{ maxWidth: '900px', margin: '0 auto' }}>
            <div
              style={{
                backgroundColor: 'var(--bg-surface)',
                padding: '24px',
                borderRadius: 'var(--radius-lg)',
                border: '1px solid var(--border-subtle)',
                marginBottom: '24px',
              }}
            >
              <h3 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 6px', color: 'var(--text-primary)' }}>
                Immutable Provenance Explorer
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '0 0 16px' }}>
                Look up the authentic genesis of any published institutional record: source file, cryptographic hash,
                exact spreadsheet coordinates, and authorizing officer.
              </p>

              <form onSubmit={handleProvenanceSearch}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr auto', gap: '12px', alignItems: 'flex-end' }}>
                  <Select
                    label="Authoritative Entity"
                    value={provTable}
                    onChange={(e) => setProvTable(e.target.value)}
                    options={[
                      { value: 'students', label: 'Students (students table)' },
                      { value: 'courses', label: 'Courses (courses table)' },
                      { value: 'users', label: 'Users (users table)' },
                      { value: 'departments', label: 'Departments (departments table)' },
                    ]}
                  />

                  <Input
                    label="Record UUID *"
                    placeholder="e.g. 9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
                    value={provRecordId}
                    onChange={(e) => setProvRecordId(e.target.value)}
                    required
                  />

                  <Button type="submit" variant="primary" disabled={isProvLoading || !provRecordId.trim()}>
                    {isProvLoading ? 'Tracing...' : 'Trace Genesis'}
                  </Button>
                </div>
              </form>
            </div>

            {/* Results */}
            {isProvLoading ? (
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                Querying immutable provenance chain...
              </div>
            ) : provSearched && provResults.length === 0 ? (
              <EmptyState
                title="No Provenance Record Found"
                description={`No recorded ingestion genesis exists for ${provTable} record '${provRecordId}'. If this record was created manually or before V2 provenance tracking, genesis data is unavailable.`}
              />
            ) : provResults.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                {provResults.map((p) => (
                  <div
                    key={p.id}
                    style={{
                      padding: '20px',
                      borderRadius: 'var(--radius-md)',
                      backgroundColor: 'var(--bg-surface)',
                      border: '1px solid var(--border-default)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 700, fontSize: '15px', color: 'var(--text-primary)' }}>
                        Source File: {p.original_filename}
                      </span>
                      <Badge variant="success">Verified Genesis</Badge>
                    </div>

                    <div
                      style={{
                        marginTop: '12px',
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                        gap: '12px',
                        fontSize: '12px',
                      }}
                    >
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Source Coordinate: </span>
                        <strong>{p.coordinate_reference || 'N/A'}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Source Type: </span>
                        <strong>{p.source_type}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Published At: </span>
                        <strong>{new Date(p.published_at).toLocaleString()}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-muted)' }}>Approver User ID: </span>
                        <strong>{p.approved_by || 'System Admin'}</strong>
                      </div>
                    </div>

                    <div style={{ marginTop: '12px' }}>
                      <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>
                        Cryptographic SHA-256 Checksum:
                      </span>
                      <code
                        style={{
                          fontSize: '11px',
                          color: 'var(--text-primary)',
                          fontFamily: 'var(--font-mono)',
                          wordBreak: 'break-all',
                        }}
                      >
                        {p.file_sha256}
                      </code>
                    </div>

                    {p.snapshot_payload && Object.keys(p.snapshot_payload).length > 0 && (
                      <div style={{ marginTop: '12px' }}>
                        <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>
                          Ingestion Snapshot Values:
                        </span>
                        <pre
                          style={{
                            padding: '10px',
                            backgroundColor: 'var(--bg-surface-elevated)',
                            borderRadius: 'var(--radius-sm)',
                            fontSize: '11px',
                            fontFamily: 'var(--font-mono)',
                            color: 'var(--text-primary)',
                            overflowX: 'auto',
                            maxHeight: '160px',
                          }}
                        >
                          {JSON.stringify(p.snapshot_payload, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        )}
      </div>

      {/* =================================================================== */}
      {/* DIALOG: APPROVAL / REJECTION WORKFLOW */}
      {/* =================================================================== */}
      {approvalModalBatch && (
        <Dialog
          isOpen={!!approvalModalBatch}
          onClose={() => setApprovalModalBatch(null)}
          title={`Human Review & Sign-Off: Batch ${approvalModalBatch.batch_number}`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: 0 }}>
              Review the batch validation metrics before signing off. Authoritative records will remain quarantined
              until published by an authorized administrator.
            </p>

            <div
              style={{
                padding: '12px',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--bg-surface-elevated)',
                fontSize: '12px',
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '8px',
                textAlign: 'center',
              }}
            >
              <div>
                <span style={{ color: 'var(--text-muted)', display: 'block' }}>Total Rows</span>
                <strong style={{ fontSize: '16px' }}>{approvalModalBatch.total_records}</strong>
              </div>
              <div>
                <span style={{ color: 'var(--status-success)', display: 'block' }}>Valid</span>
                <strong style={{ fontSize: '16px', color: 'var(--status-success)' }}>
                  {approvalModalBatch.valid_records}
                </strong>
              </div>
              <div>
                <span style={{ color: 'var(--status-danger)', display: 'block' }}>Errors</span>
                <strong style={{ fontSize: '16px', color: 'var(--status-danger)' }}>
                  {approvalModalBatch.error_records}
                </strong>
              </div>
            </div>

            <div>
              <Select
                label="Decision *"
                value={approvalDecision}
                onChange={(e) => setApprovalDecision(e.target.value as any)}
                options={[
                  { value: 'APPROVED', label: 'APPROVE — Quarantine cleared for publication' },
                  { value: 'REJECTED', label: 'REJECT — Quarantined rows rejected' },
                ]}
              />
            </div>

            <div>
              <Input
                label="Digital Signature / Officer Name *"
                value={approvalSignature}
                onChange={(e) => setApprovalSignature(e.target.value)}
                placeholder="e.g. Dr. Rajesh Sharma (Dean of Academics)"
                required
              />
            </div>

            <div>
              <label
                style={{
                  display: 'block',
                  fontSize: '13px',
                  fontWeight: 600,
                  marginBottom: '6px',
                  color: 'var(--text-primary)',
                }}
              >
                Governance Notes (Optional)
              </label>
              <textarea
                value={approvalNotes}
                onChange={(e) => setApprovalNotes(e.target.value)}
                placeholder="Audit notes or justifications..."
                style={{
                  width: '100%',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-default)',
                  backgroundColor: 'var(--bg-surface-elevated)',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                  fontFamily: 'inherit',
                  minHeight: '60px',
                }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px', marginTop: '8px' }}>
              <Button variant="outline" onClick={() => setApprovalModalBatch(null)}>
                Cancel
              </Button>
              <Button
                variant={approvalDecision === 'APPROVED' ? 'primary' : 'danger'}
                onClick={handleApprovalSubmit}
                disabled={isSubmittingApproval || !approvalSignature.trim()}
              >
                {isSubmittingApproval
                  ? 'Recording Decision...'
                  : `Confirm ${approvalDecision === 'APPROVED' ? 'Approval' : 'Rejection'}`}
              </Button>
            </div>
          </div>
        </Dialog>
      )}

      {/* =================================================================== */}
      {/* DIALOG: RECORD PAYLOAD INSPECTOR */}
      {/* =================================================================== */}
      {inspectingRecord && (
        <Dialog
          isOpen={!!inspectingRecord}
          onClose={() => setInspectingRecord(null)}
          title={`Row Inspection: ${inspectingRecord.extraction_coordinate}`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <Badge variant={getStatusBadgeVariant(inspectingRecord.stage_status)}>
                {inspectingRecord.stage_status}
              </Badge>
              <Badge variant="outline">{inspectingRecord.target_entity_type}</Badge>
            </div>

            {/* Validation messages */}
            {inspectingRecord.validation_results && inspectingRecord.validation_results.length > 0 && (
              <div>
                <h5 style={{ margin: '0 0 6px', fontSize: '13px', color: 'var(--text-primary)' }}>
                  Deterministic Validation Findings
                </h5>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {inspectingRecord.validation_results.map((v, i) => (
                    <div
                      key={v.id || i}
                      style={{
                        padding: '8px 12px',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor:
                          v.severity === 'ERROR'
                            ? 'var(--status-danger-subtle)'
                            : 'var(--status-warning-subtle)',
                        fontSize: '12px',
                        color:
                          v.severity === 'ERROR' ? 'var(--status-danger)' : 'var(--status-warning)',
                      }}
                    >
                      <strong>[{v.rule_code}]</strong> Field &apos;{v.field_name}&apos;: {v.message}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Normalized Payload */}
            <div>
              <h5 style={{ margin: '0 0 6px', fontSize: '13px', color: 'var(--text-primary)' }}>
                Normalized Canonical Payload
              </h5>
              <pre
                style={{
                  padding: '12px',
                  backgroundColor: 'var(--bg-surface-elevated)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '12px',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-primary)',
                  maxHeight: '180px',
                  overflowY: 'auto',
                }}
              >
                {JSON.stringify(inspectingRecord.normalized_payload, null, 2)}
              </pre>
            </div>

            {/* Raw Payload */}
            <div>
              <h5 style={{ margin: '0 0 6px', fontSize: '13px', color: 'var(--text-primary)' }}>
                Raw Original Row Values
              </h5>
              <pre
                style={{
                  padding: '12px',
                  backgroundColor: 'var(--bg-surface-elevated)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '12px',
                  fontFamily: 'var(--font-mono)',
                  color: 'var(--text-muted)',
                  maxHeight: '140px',
                  overflowY: 'auto',
                }}
              >
                {JSON.stringify(inspectingRecord.raw_payload, null, 2)}
              </pre>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="outline" onClick={() => setInspectingRecord(null)}>
                Close
              </Button>
            </div>
          </div>
        </Dialog>
      )}

      {/* =================================================================== */}
      {/* DIALOG: REGISTER DATA SOURCE */}
      {/* =================================================================== */}
      {isCreateSourceOpen && (
        <Dialog
          isOpen={isCreateSourceOpen}
          onClose={() => setIsCreateSourceOpen(false)}
          title="Register Institutional Data Source"
        >
          <form onSubmit={handleCreateSource}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <Input
                label="Data Source Name *"
                placeholder="e.g. Registrar ERP SIS Daily Sync"
                value={sourceName}
                onChange={(e) => setSourceName(e.target.value)}
                required
              />

              <Select
                label="Source Feed Type *"
                value={sourceType}
                onChange={(e) => setSourceType(e.target.value)}
                options={[
                  { value: 'CSV_UPLOAD', label: 'CSV / Delimited File Upload' },
                  { value: 'SPREADSHEET_UPLOAD', label: 'Spreadsheet Upload' },
                  { value: 'SIS_SYNC', label: 'SIS / ERP Database Sync' },
                  { value: 'LMS_EXPORT', label: 'LMS Gradebook Export' },
                  { value: 'EXTERNAL_API', label: 'External Institutional API' },
                ]}
              />

              <div>
                <label
                  style={{
                    display: 'block',
                    fontSize: '13px',
                    fontWeight: 600,
                    marginBottom: '6px',
                    color: 'var(--text-primary)',
                  }}
                >
                  Connection Details (JSON)
                </label>
                <textarea
                  value={sourceConnectionDetails}
                  onChange={(e) => setSourceConnectionDetails(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-default)',
                    backgroundColor: 'var(--bg-surface-elevated)',
                    color: 'var(--text-primary)',
                    fontSize: '12px',
                    fontFamily: 'var(--font-mono)',
                    minHeight: '70px',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <Button variant="outline" type="button" onClick={() => setIsCreateSourceOpen(false)}>
                  Cancel
                </Button>
                <Button variant="primary" type="submit" disabled={isCreatingSource || !sourceName.trim()}>
                  {isCreatingSource ? 'Registering...' : 'Register Source'}
                </Button>
              </div>
            </div>
          </form>
        </Dialog>
      )}
    </div>
  );
}
