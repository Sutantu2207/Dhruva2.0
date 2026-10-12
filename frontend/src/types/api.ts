/**
 * Dhruva.AI V2 — Standardized API Envelope & Error Types
 */

export interface PaginationMeta {
  page: number;
  page_size: number;
  total_items: number;
  total_pages: number;
  has_next: boolean;
  has_prev: boolean;
}

export interface ResponseMeta {
  request_id: string;
  timestamp: string;
  pagination?: PaginationMeta | null;
}

export interface ApiResponse<T = unknown> {
  success: true;
  data: T;
  meta: ResponseMeta;
}

export interface ErrorDetail {
  field?: string;
  issue: string;
}

export interface ErrorBody {
  code: string;
  message: string;
  details: ErrorDetail[];
  request_id: string;
}

export interface ApiErrorResponse {
  success: false;
  error: ErrorBody;
}
