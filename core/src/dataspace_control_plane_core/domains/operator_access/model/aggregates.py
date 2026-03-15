from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone

from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId
from .enums import GrantStatus
from .value_objects import Role, Scope, Permission, PermissionAction


@dataclass(frozen=True)
class OperatorPrincipal:
    """
    Normalized operator identity. Created from a Keycloak JWT by the adapter layer.
    Never store session tokens, refresh tokens, or Keycloak realm config here.
    """
    subject: str
    email: str | None
    realm_roles: frozenset[str]
    client_roles: frozenset[str]
    tenant_ids: frozenset[str]

    def has_realm_role(self, role: str) -> bool:
        return role in self.realm_roles

    def can_access_tenant(self, tenant_id: str) -> bool:
        return tenant_id in self.tenant_ids or "platform_admin" in self.realm_roles


@dataclass(frozen=True)
class Grant:
    """An explicit authorization grant for a principal on a resource."""
    grant_id: str
    subject: str
    role_name: str
    scope: Scope
    granted_by: str
    granted_at: datetime
    expires_at: datetime | None = None
    status: GrantStatus = GrantStatus.ACTIVE

    def is_active(self, now: datetime) -> bool:
        if self.status != GrantStatus.ACTIVE:
            return False
        if self.expires_at and self.expires_at < now:
            return False
        return True


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str
    grant_id: str | None = None


@dataclass(frozen=True)
class EmergencyAccessGrant:
    """Time-limited emergency access grant, requires justification and auditing."""
    grant_id: str
    subject: str
    justification: str
    approved_by: str
    granted_at: datetime
    expires_at: datetime
    scope: Scope
