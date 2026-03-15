from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot
from dataspace_control_plane_core.domains._shared.ids import (
    AggregateId, TenantId, LegalEntityId, SiteId, EnvironmentId
)
from dataspace_control_plane_core.domains._shared.time import utc_now
from .enums import TenantStatus, EnvironmentTier
from .value_objects import Address, ExternalIdentifier


@dataclass(frozen=True)
class EnterpriseGroup:
    group_id: str
    display_name: str
    tenant_ids: tuple[TenantId, ...] = ()


@dataclass(frozen=True)
class Tenant:
    tenant_id: TenantId
    display_name: str
    status: TenantStatus = TenantStatus.PENDING


@dataclass(frozen=True)
class LegalEntity:
    legal_entity_id: LegalEntityId
    display_name: str
    registered_name: str
    address: Address | None = None
    external_identifiers: tuple[ExternalIdentifier, ...] = ()


@dataclass
class Site:
    """A physical or logical site within a legal entity."""
    site_id: SiteId
    legal_entity_id: LegalEntityId
    display_name: str
    address: Address | None = None
    external_identifiers: list[ExternalIdentifier] = field(default_factory=list)
    is_active: bool = True


@dataclass
class Environment:
    """A deployment environment owned by a legal entity."""
    environment_id: EnvironmentId
    legal_entity_id: LegalEntityId
    tier: EnvironmentTier
    display_name: str
    connector_url: str | None = None
    is_active: bool = True


@dataclass
class LegalEntityTopology(AggregateRoot):
    """
    Aggregate root for a legal entity's enterprise hierarchy.
    Owns sites, environments, and external identifiers.
    tenant_id and legal_entity_id together form the partition key.
    """
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId("__unset__"))
    display_name: str = ""
    registered_name: str = ""
    address: Address | None = None
    external_identifiers: list[ExternalIdentifier] = field(default_factory=list)
    sites: list[Site] = field(default_factory=list)
    environments: list[Environment] = field(default_factory=list)
    status: TenantStatus = TenantStatus.PENDING
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def add_external_identifier(self, identifier: ExternalIdentifier) -> None:
        """Add or replace an external identifier by scheme+value."""
        self.external_identifiers = [
            e for e in self.external_identifiers
            if not (e.scheme == identifier.scheme and e.value == identifier.value)
        ]
        self.external_identifiers.append(identifier)

    def activate(self) -> None:
        from .invariants import require_minimum_identifiers
        require_minimum_identifiers(self)
        self.status = TenantStatus.ACTIVE
        self.updated_at = utc_now()

    def suspend(self, reason: str) -> None:
        self.status = TenantStatus.SUSPENDED
        self.updated_at = utc_now()

    def register_site(self, site: Site) -> None:
        self.sites = [existing for existing in self.sites if existing.site_id != site.site_id]
        self.sites.append(site)
        self.updated_at = utc_now()

    def register_environment(self, environment: Environment) -> None:
        self.environments = [
            existing
            for existing in self.environments
            if existing.environment_id != environment.environment_id
        ]
        self.environments.append(environment)
        self.updated_at = utc_now()

    def get_identifier(self, scheme: str) -> ExternalIdentifier | None:
        return next((e for e in self.external_identifiers if e.scheme == scheme), None)

    def to_snapshot(self) -> "TopologySnapshot":
        from .value_objects import TopologySnapshot
        return TopologySnapshot(
            tenant_id=self.tenant_id,
            legal_entity_id=self.legal_entity_id,
            display_name=self.display_name,
            external_identifiers=tuple(self.external_identifiers),
            site_ids=tuple(s.site_id for s in self.sites),
        )


TenantTopology = LegalEntityTopology
