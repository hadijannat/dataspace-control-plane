"""Domain services for the twins domain."""
from __future__ import annotations

from dataspace_control_plane_core.domains._shared.ids import AggregateId
from dataspace_control_plane_core.domains._shared.time import Clock, UtcClock
from .commands import (
    RegisterTwinCommand,
    PublishTwinCommand,
    UpdateTwinDescriptorCommand,
    DeprecateTwinCommand,
)
from .model.aggregates import TwinAsset
from .model.value_objects import TwinVersion
from .model.enums import TwinLifecycleState
from .ports import TwinRepository, AasRegistryPort


class TwinPublicationService:
    """
    Orchestrates the twin lifecycle: registration, publication, descriptor updates,
    and deprecation. All persistence is delegated to TwinRepository. AAS Registry
    synchronisation happens through AasRegistryPort after a successful save.
    """

    def __init__(
        self,
        repo: TwinRepository,
        registry: AasRegistryPort,
        clock: Clock = UtcClock(),
    ) -> None:
        self._repo = repo
        self._registry = registry
        self._clock = clock

    async def register_twin(self, cmd: RegisterTwinCommand) -> TwinAsset:
        """Create a new twin aggregate in DRAFT state with no descriptor."""
        twin = TwinAsset(
            id=AggregateId.generate(),
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
            global_asset_id=cmd.global_asset_id,
            version=TwinVersion(major=1, minor=0, patch=0),
            lifecycle=TwinLifecycleState.DRAFT,
            visibility=cmd.visibility,
        )
        await self._repo.save(cmd.tenant_id, twin)
        return twin

    async def publish_twin(self, cmd: PublishTwinCommand) -> TwinAsset:
        """
        Load the twin, call publish(), persist it, then register the shell
        with the external AAS registry.
        """
        twin = await self._repo.get(cmd.tenant_id, cmd.twin_id)
        twin.publish(cmd.descriptor, cmd.actor)
        await self._repo.save(cmd.tenant_id, twin)
        await self._registry.register_shell(cmd.tenant_id, cmd.descriptor)
        return twin

    async def update_descriptor(self, cmd: UpdateTwinDescriptorCommand) -> TwinAsset:
        """Replace the descriptor (bumps minor version) and persist."""
        twin = await self._repo.get(cmd.tenant_id, cmd.twin_id)
        twin.update_descriptor(cmd.descriptor, cmd.actor)
        await self._repo.save(cmd.tenant_id, twin)
        return twin

    async def deprecate_twin(self, cmd: DeprecateTwinCommand) -> TwinAsset:
        """Move the twin to DEPRECATED state and persist."""
        twin = await self._repo.get(cmd.tenant_id, cmd.twin_id)
        twin.deprecate()
        await self._repo.save(cmd.tenant_id, twin)
        return twin
