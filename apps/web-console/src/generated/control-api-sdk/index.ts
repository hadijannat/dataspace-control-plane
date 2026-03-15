// Generated from control-api /openapi.json — regenerate with: pnpm run gen:api
// TODO: wire openapi-ts or openapi-generator in CI

export interface ProcedureHandle {
  workflow_id: string;
  procedure_type: string;
  tenant_id: string;
  status: string;
  poll_url: string;
  stream_url: string;
  correlation_id?: string;
  started_at?: string;
}

export interface ProcedureStatus {
  workflow_id: string;
  procedure_type: string;
  tenant_id: string;
  status: 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED' | 'TERMINATED' | 'TIMED_OUT';
  result?: unknown;
  failure_message?: string;
  search_attributes?: Record<string, unknown>;
  started_at?: string;
  updated_at?: string;
}

export interface Tenant {
  tenant_id: string;
  display_name: string;
  legal_entity_id?: string;
  status: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

// API client functions — implementations delegate to apiFetch from shared/api
import { apiFetch } from '../../shared/api';

function withQuery(path: string, params?: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params ?? {})) {
    if (value !== undefined) {
      search.set(key, String(value));
    }
  }
  const query = search.toString();
  return query ? `${path}?${query}` : path;
}

export const proceduresApi = {
  start: (body: { procedure_type: string; tenant_id: string; legal_entity_id?: string; payload?: Record<string, unknown>; idempotency_key?: string }): Promise<ProcedureHandle> =>
    apiFetch('/api/v1/operator/procedures/start', { method: 'POST', body }),

  getStatus: (workflowId: string): Promise<ProcedureStatus> =>
    apiFetch(`/api/v1/operator/procedures/${workflowId}`),

  list: (tenantId: string, params?: { status?: string; limit?: number; offset?: number }): Promise<PaginatedResponse<ProcedureStatus>> =>
    apiFetch(withQuery('/api/v1/operator/procedures', { tenant_id: tenantId, ...params })),
};

export const tenantsApi = {
  list: (params?: { limit?: number; offset?: number }): Promise<PaginatedResponse<Tenant>> =>
    apiFetch(withQuery('/api/v1/operator/tenants', params)),

  get: (tenantId: string): Promise<Tenant> =>
    apiFetch(`/api/v1/operator/tenants/${tenantId}`),
};
