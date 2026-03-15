/**
 * AuthProvider: initializes Keycloak, bootstraps the session,
 * sets up token refresh, and blocks rendering until auth is ready.
 */
import { createContext, useContext, useEffect, useState, type ReactNode } from 'react';
import { createKeycloakInstance } from './keycloak';
import { setSession, getSession, type SessionState } from './session-store';

interface AuthContextValue {
  session: Readonly<SessionState>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [session, setSessionState] = useState<Readonly<SessionState>>(getSession());

  useEffect(() => {
    const kc = createKeycloakInstance();

    kc.init({ onLoad: 'login-required', pkceMethod: 'S256' })
      .then((authenticated) => {
        if (authenticated) {
          const parsed = kc.tokenParsed ?? {};
          setSession({
            authenticated: true,
            subject: kc.subject ?? null,
            email: (parsed['email'] as string | undefined) ?? null,
            realmRoles: (parsed['realm_access'] as { roles?: string[] } | undefined)?.roles ?? [],
            tenantIds: (parsed['tenant_ids'] as string[] | undefined) ?? [],
            accessToken: kc.token ?? null,
          });
          setSessionState(getSession());
        }
        setReady(true);
      })
      .catch((err) => {
        console.error('Keycloak init failed', err);
        setReady(true);
      });

    // Token refresh: refresh 60s before expiry
    kc.onTokenExpired = () => {
      kc.updateToken(60).then((refreshed) => {
        if (refreshed) {
          setSession({ accessToken: kc.token ?? null });
          setSessionState(getSession());
        }
      });
    };
  }, []);

  const logout = () => {
    const kc = createKeycloakInstance();
    kc.logout();
  };

  if (!ready) {
    return <div>Authenticating...</div>;
  }

  return (
    <AuthContext.Provider value={{ session, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider');
  return ctx;
}

export function useActiveTenantId(): string | null {
  const { session } = useAuth();
  return session.tenantIds[0] ?? null;
}
