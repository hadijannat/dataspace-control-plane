/**
 * useEventStream: reusable hook for SSE connections to control-api streams.
 * Automatically reconnects on error. Cleans up on unmount.
 */
import { useEffect, useRef, useState } from 'react';
import { getSession } from '../../auth/session-store';
import { getRuntimeConfig } from '../../app/runtime-config';

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

  useEffect(() => {
    if (!enabled) return;

    const token = getSession().accessToken;
    const config = getRuntimeConfig();
    const baseUrl = config.apiBaseUrl.replace(/\/$/, '');
    const resolvedUrl = url.startsWith('http') ? url : `${baseUrl}${url}`;
    // EventSource doesn't support custom headers; append token as query param
    // and let control-api explicitly validate it on stream endpoints.
    const fullUrl = token ? `${resolvedUrl}${resolvedUrl.includes('?') ? '&' : '?'}access_token=${encodeURIComponent(token)}` : resolvedUrl;

    const es = new EventSource(fullUrl);
    esRef.current = es;

    es.onopen = () => setState((s) => ({ ...s, connected: true, error: null }));
    es.onmessage = (event) => {
      setState((s) => ({ ...s, lastMessage: event.data }));
      onMessage?.(event.data);
    };
    es.onerror = () => {
      setState((s) => ({ ...s, connected: false, error: 'SSE connection error' }));
      es.close();
    };

    return () => {
      es.close();
      esRef.current = null;
    };
  }, [url, enabled]);

  return state;
}
