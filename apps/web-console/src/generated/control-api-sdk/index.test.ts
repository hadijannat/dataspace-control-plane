import { afterEach, describe, expect, it, vi } from 'vitest';

import { setSession, clearSession } from '../../auth/session-store';
import { proceduresApi, streamsApi, tenantsApi } from './index';

vi.mock('../../app/runtime-config', () => ({
  getRuntimeConfig: () => ({
    apiBaseUrl: 'http://control-api.test',
    keycloakUrl: 'http://keycloak.test',
    keycloakRealm: 'dataspace',
    keycloakClientId: 'web-console',
  }),
}));

describe('control-api sdk', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    clearSession();
  });

  it('uses the operator procedures list contract', async () => {
    setSession({ authenticated: true, accessToken: 'token-123' });
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ items: [], total: 0, limit: 50, offset: 0 }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await proceduresApi.list('tenant-a', { status: 'RUNNING', limit: 25, offset: 50 });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://control-api.test/api/v1/operator/procedures/?tenant_id=tenant-a&status=RUNNING&limit=25&offset=50',
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: 'Bearer token-123',
        }),
      }),
    );
  });

  it('uses the paginated tenants contract', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ items: [], total: 0, limit: 50, offset: 0 }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await tenantsApi.list({ limit: 10, offset: 20 });

    expect(fetchMock).toHaveBeenCalledWith(
      'http://control-api.test/api/v1/operator/tenants/?limit=10&offset=20',
      expect.any(Object),
    );
  });

  it('issues short-lived stream tickets over the authenticated API channel', async () => {
    setSession({ authenticated: true, accessToken: 'ticket-token' });
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ ticket: 'ticket-123', expires_in_seconds: 300 }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await streamsApi.issueTicket();

    expect(fetchMock).toHaveBeenCalledWith(
      'http://control-api.test/api/v1/streams/tickets',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer ticket-token',
        }),
      }),
    );
  });
});
