"""Port interfaces for the schema_mapping domain. Adapters implement these."""
from __future__ import annotations
from typing import Protocol, runtime_checkable

from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId
from .model.aggregates import SchemaMapping


@runtime_checkable
class SchemaMappingRepository(Protocol):
    """Persistence port for SchemaMapping aggregates."""

    async def get(self, tenant_id: TenantId, mapping_id: AggregateId) -> SchemaMapping:
        """Load a SchemaMapping; raises MappingNotFoundError if absent."""
        ...

    async def save(self, tenant_id: TenantId, mapping: SchemaMapping) -> None:
        """Persist the mapping with optimistic concurrency."""
        ...

    async def find_by_schemas(
        self, tenant_id: TenantId, source_id: str, target_id: str
    ) -> SchemaMapping | None:
        """Return the mapping for the given schema pair, or None."""
        ...


@runtime_checkable
class SchemaRegistryPort(Protocol):
    """Cross-boundary port: access schema definitions from an external schema registry."""

    async def get_schema(self, schema_id: str) -> dict:
        """Retrieve the raw JSON Schema document for the given schema ID."""
        ...

    async def validate_against_schema(self, instance: dict, schema_id: str) -> bool:
        """Return True if instance validates against the schema, False otherwise."""
        ...
