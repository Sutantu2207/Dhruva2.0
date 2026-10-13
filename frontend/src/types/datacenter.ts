/**
 * Dhruva.AI V2 — Data Center, Ingestion Pipeline & Provenance TypeScript Definitions
 * 
 * Strictly typed interfaces matching backend Pydantic schemas in src.interfaces.http.schemas.ingestion.
 */

export type SourceType =
  | 'CSV_UPLOAD'
  | 'SPREADSHEET_UPLOAD'
  | 'SIS_SYNC'
  | 'LMS_EXPORT'
  | 'EXTERNAL_API';

export type TargetDomain = 'STUDENTS' | 'COURSES' | 'FACULTY';

export type BatchStatus =
  | 'UPLOADED'
  | 'STAGED'
  | 'APPROVED'
  | 'REJECTED'
  | 'PUBLISHED'
  | 'ROLLED_BACK';

export type StageStatus =
  | 'PENDING'
  | 'VALID'
  | 'WARNING'
  | 'ERROR'
  | 'APPROVED'
  | 'REJECTED'
  | 'PUBLISHED'
  | 'ROLLED_BACK';

export type SeverityLevel = 'ERROR' | 'WARNING' | 'INFO';

export interface DataSource {
  id: string;
  institution_id: string;
  name: string;
  source_type: SourceType | string;
  connection_details: Record<string, unknown>;
  status: 'ACTIVE' | 'INACTIVE';
  created_at: string;
  updated_at: string;
}

export interface DataSourceCreateInput {
  name: string;
  source_type: SourceType | string;
  connection_details?: Record<string, unknown>;
}

export interface ValidationResult {
  id: string;
  staged_record_id: string;
  rule_code: string;
  severity: SeverityLevel | string;
  field_name: string;
  message: string;
  context: Record<string, unknown>;
  checked_at: string;
}

export interface StagedRecord {
  id: string;
  institution_id: string;
  import_batch_id: string;
  row_index: number;
  target_entity_type: string;
  raw_payload: Record<string, string>;
  normalized_payload: Record<string, unknown>;
  extraction_coordinate: string;
  stage_status: StageStatus | string;
  created_at: string;
  updated_at: string;
  validation_results: ValidationResult[];
}

export interface ImportBatch {
  id: string;
  institution_id: string;
  data_source_id?: string | null;
  batch_number: string;
  original_file_name: string;
  file_sha256: string;
  storage_uri: string;
  file_size_bytes: number;
  mime_type: string;
  total_records: number;
  valid_records: number;
  warning_records: number;
  error_records: number;
  status: BatchStatus | string;
  target_domain: TargetDomain | string;
  uploaded_by?: string | null;
  error_summary: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Approval {
  id: string;
  institution_id: string;
  import_batch_id: string;
  reviewer_user_id?: string | null;
  decision: 'APPROVED' | 'REJECTED';
  digital_signature: string;
  notes: string;
  decided_at: string;
}

export interface ApprovalInput {
  decision: 'APPROVED' | 'REJECTED';
  digital_signature: string;
  notes?: string;
}

export interface ProvenanceRecord {
  id: string;
  institution_id: string;
  authoritative_table: string;
  authoritative_record_id: string;
  import_batch_id?: string | null;
  staged_record_id?: string | null;
  approved_by?: string | null;
  source_type: string;
  original_filename: string;
  file_sha256: string;
  coordinate_reference: string;
  snapshot_payload: Record<string, unknown>;
  published_at: string;
}

export interface DataCenterTelemetry {
  total_batches: number;
  pending_approval: number;
  published_batches: number;
  total_records: number;
  valid_records: number;
  warning_records: number;
  error_records: number;
  failure_rate_percent: number;
  active_data_sources: number;
  total_provenance_records: number;
}
