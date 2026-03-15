/**
 * In-memory session store.
 * Tokens are kept only in memory — never in localStorage or sessionStorage.
 * Access token is short-lived; refresh is handled centrally in auth-provider.
 */
export interface SessionState {
  authenticated: boolean;
  subject: string | null;
  email: string | null;
  realmRoles: string[];
  tenantIds: string[];
  accessToken: string | null;
}

const _initial: SessionState = {
  authenticated: false,
  subject: null,
  email: null,
  realmRoles: [],
  tenantIds: [],
  accessToken: null,
};

let _session: SessionState = { ..._initial };

export function getSession(): Readonly<SessionState> {
  return _session;
}

export function setSession(partial: Partial<SessionState>): void {
  _session = { ..._session, ...partial };
}

export function clearSession(): void {
  _session = { ..._initial };
}
