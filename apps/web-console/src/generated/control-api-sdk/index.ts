// This file is generated from apps/control-api OpenAPI. Do not edit manually.

import { apiFetch } from '../../shared/api';

export interface AcceptedResponse {
  "workflow_id": string;
  "status"?: string;
  "poll_url": string;
  "stream_url": string;
  "correlation_id"?: string | null;
}

export interface HTTPValidationError {
  "detail"?: ValidationError[];
}

export interface HealthResponse {
  "status": string;
  "version"?: string;
  "dependencies"?: Record<string, boolean> | null;
}

export interface PaginatedResponse_TenantSummary_ {
  "items": TenantSummary[];
  "total": number;
  "limit": number;
  "offset": number;
}

export interface ProcedureHandleDTO {
  "workflow_id": string;
  "procedure_type": string;
  "tenant_id": string;
  "status": string;
  "poll_url": string;
  "stream_url": string;
  "correlation_id"?: string | null;
  "started_at"?: string | null;
}

export interface ProcedureListDTO {
  "items": ProcedureStatusDTO[];
  "total": number;
  "limit": number;
  "offset": number;
}

export interface ProcedureStatusDTO {
  "workflow_id": string;
  "procedure_type": string;
  "tenant_id": string;
  "status": string;
  "result"?: unknown | null;
  "failure_message"?: string | null;
  "search_attributes"?: Record<string, unknown>;
  "started_at"?: string | null;
  "updated_at"?: string | null;
}

export interface PublicStartProcedureRequest {
  "procedure_type": string;
  "tenant_id": string;
  "legal_entity_id"?: string | null;
  "payload"?: Record<string, unknown>;
  "idempotency_key"?: string | null;
}

export interface StartProcedureRequest {
  "procedure_type": string;
  "tenant_id": string;
  "legal_entity_id"?: string | null;
  "payload"?: Record<string, unknown>;
  "idempotency_key"?: string | null;
}

export interface StreamTicketResponse {
  "ticket": string;
  "expires_in_seconds": number;
}

export interface TenantSummary {
  "tenant_id": string;
  "display_name": string;
  "status": string;
  "legal_entity_id"?: string | null;
}

export interface ValidationError {
  "loc": (string | number)[];
  "msg": string;
  "type": string;
  "input"?: unknown;
  "ctx"?: Record<string, unknown>;
}

export interface WebhookAcceptedResponse {
  "accepted"?: boolean;
  "correlation_id"?: string | null;
}

export type ProcedureHandle = ProcedureHandleDTO;
export type ProcedureStatus = ProcedureStatusDTO;
export type Tenant = TenantSummary;

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
  start: (body: StartProcedureRequest): Promise<ProcedureHandleDTO> =>
    apiFetch('/api/v1/operator/procedures/start', { method: 'POST', body }),
  list: (tenantId: string, params?: { status?: string; limit?: number; offset?: number }): Promise<ProcedureListDTO> =>
    apiFetch(withQuery('/api/v1/operator/procedures/', { tenant_id: tenantId, ...params })),
  getStatus: (workflowId: string): Promise<ProcedureStatusDTO> =>
    apiFetch('/api/v1/operator/procedures/{workflow_id}'.replace('{workflow_id}', encodeURIComponent(workflowId))),
};

export const tenantsApi = {
  list: (params?: { limit?: number; offset?: number }): Promise<PaginatedResponse_TenantSummary_> =>
    apiFetch(withQuery('/api/v1/operator/tenants/', params)),
  get: (tenantId: string): Promise<TenantSummary> =>
    apiFetch('/api/v1/operator/tenants/{tenant_id}'.replace('{tenant_id}', encodeURIComponent(tenantId))),
};

export const publicProceduresApi = {
  start: (body: PublicStartProcedureRequest): Promise<AcceptedResponse> =>
    apiFetch('/api/v1/public/procedures/start', { method: 'POST', body }),
  getStatus: (workflowId: string): Promise<ProcedureStatusDTO> =>
    apiFetch('/api/v1/public/procedures/{workflow_id}'.replace('{workflow_id}', encodeURIComponent(workflowId))),
};

export const streamsApi = {
  issueTicket: (): Promise<StreamTicketResponse> =>
    apiFetch('/api/v1/streams/tickets', { method: 'POST' }),
};

