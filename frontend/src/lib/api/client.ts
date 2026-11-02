/**
 * Dhruva.AI V2 — Typed HTTP API Client with Error Envelope Unwrapping
 */

import { ApiErrorResponse, ApiResponse, ErrorBody } from '@/types/api';

function getApiBaseUrl(): string {
  // 1. Server-side runtime (Next.js Functions, SSR, Server Components):
  // Reads internal service URL injected via Vercel service binding (BACKEND_URL)
  if (typeof window === 'undefined') {
    const serverUrl = process.env.BACKEND_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const clean = serverUrl.trim().replace(/\/+$/, '');
    return clean.endsWith('/api/v1') ? clean : `${clean}/api/v1`;
  }

  // 2. Client-side browser runtime with explicit external API URL override
  const clientUrl = process.env.NEXT_PUBLIC_API_URL;
  if (clientUrl) {
    const clean = clientUrl.trim().replace(/\/+$/, '');
    return clean.endsWith('/api/v1') ? clean : `${clean}/api/v1`;
  }

  // 3. Client-side browser runtime under Vercel Services (same-origin relative path rewritten to backend service)
  return '/api/v1';
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

  constructor() {
    if (typeof window !== 'undefined') {
      try {
        this.token = localStorage.getItem('dhruva_token');
      } catch {
        this.token = null;
      }
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== 'undefined') {
      try {
        if (token) {
          localStorage.setItem('dhruva_token', token);
        } else {
          localStorage.removeItem('dhruva_token');
        }
      } catch {
        // Ignore storage errors in restricted contexts
      }
    }
  }

  getToken(): string | null {
    if (this.token) return this.token;
    if (typeof window !== 'undefined') {
      try {
        this.token = localStorage.getItem('dhruva_token');
      } catch {
        // Ignore storage errors
      }
    }
    return this.token;
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

    const currentToken = this.getToken();
    if (currentToken) {
      headers['Authorization'] = `Bearer ${currentToken}`;
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

    let data: any = null;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        data = await response.json();
      } catch {
        data = null;
      }
    } else {
      try {
        const text = await response.text();
        try {
          data = JSON.parse(text);
        } catch {
          data = { message: text || response.statusText };
        }
      } catch {
        data = null;
      }
    }

    if (!response.ok || (data && data.success === false)) {
      let errorMessage = response.statusText || 'Request failed';
      let errorCode = 'HTTP_ERROR';
      let details: Array<{ field?: string; issue: string }> = [];

      if (data) {
        if (data.error) {
          errorMessage = data.error.message || errorMessage;
          errorCode = data.error.code || errorCode;
          details = data.error.details || [];
        } else if (data.detail) {
          errorMessage = typeof data.detail === 'string'
            ? data.detail
            : Array.isArray(data.detail)
            ? data.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ')
            : JSON.stringify(data.detail);
        } else if (data.message) {
          errorMessage = data.message;
        }
      }

      const errorBody: ErrorBody = {
        code: errorCode,
        message: errorMessage,
        details,
        request_id: data?.request_id || 'req_client_unknown',
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
