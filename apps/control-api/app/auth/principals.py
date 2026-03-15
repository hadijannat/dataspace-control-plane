from dataclasses import dataclass, field
from uuid import UUID


@dataclass(frozen=True)
class Principal:
    """Authenticated human or service principal extracted from a validated JWT."""
    subject: str
    email: str | None
    realm_roles: frozenset[str] = field(default_factory=frozenset)
    client_roles: frozenset[str] = field(default_factory=frozenset)
    tenant_ids: frozenset[str] = field(default_factory=frozenset)

    def has_role(self, role: str) -> bool:
        return role in self.realm_roles or role in self.client_roles

    def can_access_tenant(self, tenant_id: str) -> bool:
        return "dataspace-admin" in self.realm_roles or tenant_id in self.tenant_ids
