import { getSession } from './session-store';

export function hasRole(role: string): boolean {
  return getSession().realmRoles.includes(role);
}

export function canAccessTenant(tenantId: string): boolean {
  const s = getSession();
  return s.realmRoles.includes('dataspace-admin') || s.tenantIds.includes(tenantId);
}
