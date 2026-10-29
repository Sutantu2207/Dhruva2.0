/**
 * Dhruva.AI V2 — Typed HTTP API Client with Error Envelope Unwrapping
 */

import { ApiErrorResponse, ApiResponse, ErrorBody } from '@/types/api';

function getApiBaseUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_API_URL;
  if (!envUrl) {
    return 'http://localhost:8000/api/v1';
  }
  const clean = envUrl.trim().replace(/\/+$/, '');
  if (!clean.endsWith('/api/v1')) {
    return `${clean}/api/v1`;
  }
  return clean;
}

export class ApiError extends Error {
  code: string;
  details: Array<{ field?: string; issue: string }>;
  requestId: string;
  statusCode: number;

  constructor(body: ErrorBody, statusCode: number) {
    super(body.message);
    this.name = 'ApiError';
    this.code = body.code;
    this.details = body.details;
    this.requestId = body.request_id;
    this.statusCode = statusCode;
  }
}

class HttpClient {
  private token: string | null = null;

  setToken(token: string | null) {
    this.token = token;
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    let cleanEndpoint = endpoint.trim();
    if (cleanEndpoint.startsWith('/api/v1')) {
      cleanEndpoint = cleanEndpoint.slice(7);
    }
    if (!cleanEndpoint.startsWith('/')) {
      cleanEndpoint = `/${cleanEndpoint}`;
    }
    const baseUrl = getApiBaseUrl();
    const url = endpoint.startsWith('http://') || endpoint.startsWith('https://')
      ? endpoint
      : `${baseUrl}${cleanEndpoint}`;
    const headers: Record<string, string> = {
      Accept: 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    // Only set application/json if body is not FormData
    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
      credentials: 'include', // Support HttpOnly cookies
    };

    const response = await fetch(url, config);

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    const data = await response.json();

    if (!response.ok || data.success === false) {
      const err = data as ApiErrorResponse;
      const errorBody: ErrorBody = err.error || {
        code: 'HTTP_ERROR',
        message: response.statusText || 'Request failed',
        details: [],
        request_id: 'req_client_unknown',
      };
      throw new ApiError(errorBody, response.status);
    }

    const successData = data as ApiResponse<T>;
    const payload = successData.data;
    if (payload && (typeof payload === 'object' || Array.isArray(payload))) {
      try {
        if (!('data' in (payload as Record<string, unknown>))) {
          Object.defineProperty(payload, 'data', {
            value: payload,
            enumerable: false,
            configurable: true,
          });
        }
      } catch {
        // Ignore if non-extensible
      }
    }
    return payload;
  }

  get<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'GET' });
  }

  post<T>(endpoint: string, body?: unknown, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  put<T>(endpoint: string, body?: unknown, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  patch<T>(endpoint: string, body?: unknown, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  upload<T>(endpoint: string, formData: FormData, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, {
      ...options,
      method: 'POST',
      body: formData,
    });
  }

  delete<T>(endpoint: string, options?: RequestInit): Promise<T> {
    return this.request<T>(endpoint, { ...options, method: 'DELETE' });
  }
}

export const api = new HttpClient();
