"""Domain services for the schema_mapping domain."""
from __future__ import annotations

from dataspace_control_plane_core.domains._shared.ids import AggregateId
from dataspace_control_plane_core.domains._shared.time import Clock, UtcClock
from .commands import (
    CreateMappingCommand,
    ActivateMappingCommand,
    AddMappingRuleCommand,
)
from .model.aggregates import SchemaMapping
from .model.enums import MappingStatus
from .ports import SchemaMappingRepository


class SchemaMappingService:
    """
    Orchestrates schema mapping lifecycle: creation, activation, and rule management.
    All persistence is delegated to SchemaMappingRepository.
    """

    def __init__(
        self,
        repo: SchemaMappingRepository,
        clock: Clock = UtcClock(),
    ) -> None:
        self._repo = repo
        self._clock = clock

    async def create_mapping(self, cmd: CreateMappingCommand) -> SchemaMapping:
        """Create a new SchemaMapping aggregate in DRAFT state."""
        mapping = SchemaMapping(
            id=AggregateId.generate(),
            tenant_id=cmd.tenant_id,
            source_schema_id=cmd.source_schema_id,
            target_schema_id=cmd.target_schema_id,
            direction=cmd.direction,
            status=MappingStatus.DRAFT,
            version=1,
        )
        await self._repo.save(cmd.tenant_id, mapping)
        return mapping

    async def activate_mapping(self, cmd: ActivateMappingCommand) -> SchemaMapping:
        """Load, activate, and persist the mapping."""
        mapping = await self._repo.get(cmd.tenant_id, cmd.mapping_id)
        mapping.activate()
        await self._repo.save(cmd.tenant_id, mapping)
        return mapping

    async def add_rule(self, cmd: AddMappingRuleCommand) -> SchemaMapping:
        """Append a rule to an existing mapping (bumps version) and persist."""
        mapping = await self._repo.get(cmd.tenant_id, cmd.mapping_id)
        mapping.add_rule(cmd.rule)
        await self._repo.save(cmd.tenant_id, mapping)
        return mapping
