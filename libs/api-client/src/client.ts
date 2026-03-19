import type { ApiResponse } from '@vanta-lms/shared-types';

const BASE_URL =
  (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) ??
  'http://localhost:8000/api/v1';

export interface ApiClientOptions {
  baseUrl?: string;
  headers?: Record<string, string>;
}

export interface RequestOptions {
  headers?: Record<string, string>;
  signal?: AbortSignal;
}

export function createApiClient(options: ApiClientOptions = {}) {
  const baseUrl = options.baseUrl ?? BASE_URL;
  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  async function request<T>(
    method: string,
    path: string,
    body?: unknown,
    opts?: RequestOptions
  ): Promise<ApiResponse<T>> {
    const url = `${baseUrl}${path}`;
    const headers = { ...defaultHeaders, ...opts?.headers };

    const response = await fetch(url, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: opts?.signal,
    });

    const json = await response.json();

    if (!response.ok) {
      throw new Error(json.detail ?? json.error ?? `HTTP ${response.status}`);
    }

    return json as ApiResponse<T>;
  }

  return {
    get: <T>(path: string, opts?: RequestOptions) =>
      request<T>('GET', path, undefined, opts),
    post: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
      request<T>('POST', path, body, opts),
    put: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
      request<T>('PUT', path, body, opts),
    patch: <T>(path: string, body?: unknown, opts?: RequestOptions) =>
      request<T>('PATCH', path, body, opts),
    delete: <T>(path: string, opts?: RequestOptions) =>
      request<T>('DELETE', path, undefined, opts),
  };
}

export const client = createApiClient();
