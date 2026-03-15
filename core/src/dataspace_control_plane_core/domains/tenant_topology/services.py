from __future__ import annotations
from dataspace_control_plane_core.domains._shared.ids import AggregateId
from dataspace_control_plane_core.domains._shared.errors import NotFoundError
from dataspace_control_plane_core.domains._shared.time import Clock, UtcClock
from .commands import (
    RegisterLegalEntityCommand, AddExternalIdentifierCommand,
    ActivateLegalEntityCommand, RegisterEnvironmentCommand,
)
from .events import LegalEntityRegistered, LegalEntityActivated, ExternalIdentifierAdded, EnvironmentRegistered
from .model.aggregates import LegalEntityTopology, Environment
from .model.value_objects import ExternalIdentifier
from .ports import LegalEntityRepository


class TenantTopologyService:
    def __init__(self, repo: LegalEntityRepository, clock: Clock = UtcClock()) -> None:
        self._repo = repo
        self._clock = clock

    async def register_legal_entity(self, cmd: RegisterLegalEntityCommand) -> LegalEntityTopology:
        topology = LegalEntityTopology(
            id=AggregateId.generate(),
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
            display_name=cmd.display_name,
            registered_name=cmd.registered_name,
        )
        topology._raise_event(LegalEntityRegistered(
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
            display_name=cmd.display_name,
        ))
        await self._repo.save(topology, expected_version=0)
        return topology

    async def add_external_identifier(self, cmd: AddExternalIdentifierCommand) -> LegalEntityTopology:
        topology = await self._repo.get(cmd.tenant_id, cmd.legal_entity_id)
        identifier = ExternalIdentifier(
            scheme=cmd.scheme, value=cmd.value,
            issuer=cmd.issuer, valid_from=cmd.valid_from, valid_to=cmd.valid_to,
        )
        topology.add_external_identifier(identifier)
        topology.updated_at = self._clock.now()
        topology._raise_event(ExternalIdentifierAdded(
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
            scheme=cmd.scheme, value=cmd.value,
        ))
        await self._repo.save(topology, expected_version=topology.version)
        return topology

    async def activate_legal_entity(self, cmd: ActivateLegalEntityCommand) -> LegalEntityTopology:
        topology = await self._repo.get(cmd.tenant_id, cmd.legal_entity_id)
        topology.activate()
        topology._raise_event(LegalEntityActivated(
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
        ))
        await self._repo.save(topology, expected_version=topology.version)
        return topology

    async def register_environment(self, cmd: RegisterEnvironmentCommand) -> LegalEntityTopology:
        topology = await self._repo.get(cmd.tenant_id, cmd.legal_entity_id)
        environment = Environment(
            environment_id=cmd.environment_id,
            legal_entity_id=cmd.legal_entity_id,
            tier=cmd.tier,
            display_name=cmd.display_name,
            connector_url=cmd.connector_url,
        )
        topology.register_environment(environment)
        topology._raise_event(EnvironmentRegistered(
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
            environment_id=str(cmd.environment_id),
        ))
        await self._repo.save(topology, expected_version=topology.version)
        return topology
