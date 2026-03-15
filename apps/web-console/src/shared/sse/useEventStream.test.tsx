/** @vitest-environment jsdom */

import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useEventStream } from './useEventStream';

const { issueTicket } = vi.hoisted(() => ({
  issueTicket: vi.fn(),
}));

vi.mock('../../generated/control-api-sdk', () => ({
  streamsApi: {
    issueTicket,
  },
}));

vi.mock('../../app/runtime-config', () => ({
  getRuntimeConfig: () => ({
    apiBaseUrl: 'http://control-api.test',
    keycloakUrl: 'http://keycloak.test',
    keycloakRealm: 'dataspace',
    keycloakClientId: 'web-console',
  }),
}));

class FakeEventSource {
  static instances: FakeEventSource[] = [];

  readonly url: string;
  readonly close = vi.fn();
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onerror: (() => void) | null = null;

  constructor(url: string) {
    this.url = url;
    FakeEventSource.instances.push(this);
  }

  emitOpen() {
    this.onopen?.();
  }

  emitMessage(data: string) {
    this.onmessage?.({ data });
  }

  emitError() {
    this.onerror?.();
  }
}

async function flushMicrotasks() {
  await Promise.resolve();
  await Promise.resolve();
}

describe('useEventStream', () => {
  let scheduledReconnect: (() => void) | null;

  beforeEach(() => {
    scheduledReconnect = null;
    FakeEventSource.instances = [];
    issueTicket.mockReset();
    vi.stubGlobal('EventSource', FakeEventSource);
    vi.spyOn(window, 'setTimeout').mockImplementation(((handler: TimerHandler) => {
      if (typeof handler === 'function') {
        scheduledReconnect = () => handler();
      }
      return 1 as ReturnType<typeof window.setTimeout>;
    }) as typeof window.setTimeout);
    vi.spyOn(window, 'clearTimeout').mockImplementation(() => undefined);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it('uses a short-lived ticket and reconnects after an error', async () => {
    issueTicket
      .mockResolvedValueOnce({ ticket: 'ticket-1', expires_in_seconds: 300 })
      .mockResolvedValueOnce({ ticket: 'ticket-2', expires_in_seconds: 300 });

    const onMessage = vi.fn();
    const { result, unmount } = renderHook(() =>
      useEventStream({
        url: '/api/v1/streams/workflows/wf-123',
        onMessage,
      }),
    );

    await flushMicrotasks();

    expect(issueTicket).toHaveBeenCalledTimes(1);
    expect(FakeEventSource.instances).toHaveLength(1);
    expect(FakeEventSource.instances[0].url).toBe(
      'http://control-api.test/api/v1/streams/workflows/wf-123?ticket=ticket-1',
    );

    act(() => {
      FakeEventSource.instances[0].emitOpen();
      FakeEventSource.instances[0].emitMessage('status-update');
      FakeEventSource.instances[0].emitError();
    });

    expect(scheduledReconnect).not.toBeNull();

    scheduledReconnect?.();
    await flushMicrotasks();

    expect(issueTicket).toHaveBeenCalledTimes(2);
    expect(FakeEventSource.instances).toHaveLength(2);
    expect(FakeEventSource.instances[0].close).toHaveBeenCalled();
    expect(FakeEventSource.instances[1].url).toBe(
      'http://control-api.test/api/v1/streams/workflows/wf-123?ticket=ticket-2',
    );
    expect(result.current.lastMessage).toBe('status-update');
    expect(onMessage).toHaveBeenCalledWith('status-update');

    unmount();
    expect(FakeEventSource.instances[1].close).toHaveBeenCalled();
  });
});
