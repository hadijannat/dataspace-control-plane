/**
 * useEventStream: reusable hook for SSE connections to control-api streams.
 * Authenticates via a short-lived stream ticket rather than a bearer token in
 * the URL. Reconnects after transient failures with a fresh ticket.
 */
import { useEffect, useEffectEvent, useRef, useState } from 'react';
import { getRuntimeConfig } from '../../app/runtime-config';
import { streamsApi } from '../../generated/control-api-sdk';

export interface UseEventStreamOptions {
  url: string;
  enabled?: boolean;
  onMessage?: (data: string) => void;
}

export interface UseEventStreamState {
  connected: boolean;
  lastMessage: string | null;
  error: string | null;
}

export function useEventStream({
  url,
  enabled = true,
  onMessage,
}: UseEventStreamOptions): UseEventStreamState {
  const [state, setState] = useState<UseEventStreamState>({
    connected: false,
    lastMessage: null,
    error: null,
  });
  const esRef = useRef<EventSource | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const onMessageEvent = useEffectEvent((data: string) => {
    setState((s) => ({ ...s, lastMessage: data }));
    onMessage?.(data);
  });

  useEffect(() => {
    if (!enabled) {
      return;
    }

    let cancelled = false;
    const config = getRuntimeConfig();
    const baseUrl = config.apiBaseUrl.replace(/\/$/, '');
    const resolvedUrl = url.startsWith('http') ? url : `${baseUrl}${url}`;

    const scheduleReconnect = (message: string) => {
      setState((s) => ({ ...s, connected: false, error: message }));
      if (cancelled) {
        return;
      }
      reconnectTimerRef.current = window.setTimeout(() => {
        void connect();
      }, 1500);
    };

    const cleanupStream = () => {
      esRef.current?.close();
      esRef.current = null;
      if (reconnectTimerRef.current !== null) {
        window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };

    const connect = async () => {
      cleanupStream();
      try {
        const { ticket } = await streamsApi.issueTicket();
        if (cancelled) {
          return;
        }
        const fullUrl = `${resolvedUrl}${resolvedUrl.includes('?') ? '&' : '?'}ticket=${encodeURIComponent(ticket)}`;
        const eventSource = new EventSource(fullUrl);
        esRef.current = eventSource;

        eventSource.onopen = () => {
          setState((s) => ({ ...s, connected: true, error: null }));
        };
        eventSource.onmessage = (event) => {
          onMessageEvent(event.data);
        };
        eventSource.onerror = () => {
          eventSource.close();
          scheduleReconnect('SSE connection error');
        };
      } catch (error) {
        scheduleReconnect(error instanceof Error ? error.message : 'SSE ticket request failed');
      }
    };

    void connect();

    return () => {
      cancelled = true;
      cleanupStream();
    };
  }, [enabled, url]);

  return state;
}
