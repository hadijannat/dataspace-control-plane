from __future__ import annotations
from typing import Protocol
from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId
from .model.aggregates import LegalEntityTopology
from .model.value_objects import TopologySnapshot


class LegalEntityRepository(Protocol):
    async def get(self, tenant_id: TenantId, legal_entity_id: LegalEntityId) -> LegalEntityTopology: ...
    async def save(self, topology: LegalEntityTopology, expected_version: int) -> None: ...
    async def list(self, tenant_id: TenantId, limit: int = 50, offset: int = 0) -> list[LegalEntityTopology]: ...


class TopologyLookupPort(Protocol):
    """Read-only port for cross-domain topology queries."""
    async def get_snapshot(self, tenant_id: TenantId, legal_entity_id: LegalEntityId) -> TopologySnapshot | None: ...
    async def list_active_legal_entities(self, tenant_id: TenantId) -> list[LegalEntityId]: ...
