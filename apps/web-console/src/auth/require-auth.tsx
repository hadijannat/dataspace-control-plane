import { useAuth } from './auth-provider';
import type { ReactNode } from 'react';

export function RequireAuth({ children }: { children: ReactNode }) {
  const { session } = useAuth();
  if (!session.authenticated) {
    return <div className="p-6 text-sm text-gray-600">Authentication required. Complete the Keycloak sign-in flow to continue.</div>;
  }
  return <>{children}</>;
}
