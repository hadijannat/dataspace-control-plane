/**
 * API client wrapper.
 * The generated SDK from control-api's OpenAPI document lives in
 * src/generated/control-api-sdk/ (regenerated in CI on contract changes).
 * This module provides the shared authenticated fetch primitive used by the
 * generated client and other transport helpers.
 */
import { getSession } from '../../auth/session-store';
import { getRuntimeConfig } from '../../app/runtime-config';

interface ApiRequestInit extends Omit<RequestInit, 'body' | 'headers'> {
  body?: BodyInit | object;
  headers?: Record<string, string>;
}

function buildHeaders(init: ApiRequestInit): Record<string, string> {
  const token = getSession().accessToken;
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...((init.headers as Record<string, string>) ?? {}),
  };
}

function buildBody(init: ApiRequestInit): BodyInit | undefined {
  if (init.body === undefined || typeof init.body === 'string' || init.body instanceof FormData) {
    return init.body;
  }
  return JSON.stringify(init.body);
}

export async function apiFetch<T>(path: string, init: ApiRequestInit = {}): Promise<T> {
  const config = getRuntimeConfig();
  const response = await fetch(`${config.apiBaseUrl}${path}`, {
    ...init,
    body: buildBody(init),
    headers: buildHeaders(init),
  });
  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${await response.text()}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = { fetch: apiFetch };
