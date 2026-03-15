"""Port interfaces for the twins domain. Adapters implement these."""
from __future__ import annotations
from typing import Protocol, runtime_checkable

from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId
from .model.aggregates import TwinAsset
from .model.value_objects import TwinDescriptor, EndpointHealth


@runtime_checkable
class TwinRepository(Protocol):
    """Persistence port for TwinAsset aggregates."""

    async def get(self, tenant_id: TenantId, twin_id: AggregateId) -> TwinAsset:
        """Load a TwinAsset; raises TwinNotFoundError if absent."""
        ...

    async def save(self, tenant_id: TenantId, twin: TwinAsset) -> None:
        """Persist the twin with optimistic concurrency."""
        ...

    async def find_by_global_asset_id(
        self, tenant_id: TenantId, gaid: str
    ) -> TwinAsset | None:
        """Return the twin matching the global_asset_id, or None."""
        ...

    async def list_for_legal_entity(
        self, tenant_id: TenantId, legal_entity_id: LegalEntityId
    ) -> list[TwinAsset]:
        """Return all twins owned by the given legal entity within the tenant."""
        ...


@runtime_checkable
class AasRegistryPort(Protocol):
    """Cross-boundary port: synchronise shell descriptors with an AAS Registry."""

    async def register_shell(
        self, tenant_id: TenantId, descriptor: TwinDescriptor
    ) -> None:
        """Register or update the AAS shell in the external registry."""
        ...

    async def deregister_shell(
        self, tenant_id: TenantId, shell_id: str
    ) -> None:
        """Remove the AAS shell from the external registry."""
        ...


@runtime_checkable
class TwinEndpointProbePort(Protocol):
    """Cross-boundary port: probe the reachability of a twin endpoint URL."""

    async def probe(self, endpoint_url: str) -> EndpointHealth:
        """Return an EndpointHealth snapshot for the given URL."""
        ...


AasRepositoryPort = AasRegistryPort
SubmodelServerPort = AasRegistryPort
DigitalTwinRegistryPort = AasRegistryPort
ConnectorAssetPort = TwinEndpointProbePort
