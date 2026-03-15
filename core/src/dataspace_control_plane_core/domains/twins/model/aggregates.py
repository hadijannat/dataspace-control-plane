"""Aggregate roots for the twins domain."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone

from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.errors import ConflictError
from .enums import TwinLifecycleState, TwinVisibility
from .value_objects import TwinDescriptor, TwinVersion


@dataclass
class TwinAsset(AggregateRoot):
    """
    Aggregate root representing a Digital Twin (AAS Shell) managed by the platform.
    Tracks publication state, versioning, and endpoint descriptor.
    """
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId("__unset__"))
    global_asset_id: str = ""
    descriptor: TwinDescriptor | None = None
    version: TwinVersion = field(default_factory=lambda: TwinVersion(major=1, minor=0, patch=0))
    lifecycle: TwinLifecycleState = TwinLifecycleState.DRAFT
    visibility: TwinVisibility = TwinVisibility.PRIVATE
    published_at: datetime | None = None

    def publish(self, descriptor: TwinDescriptor, actor: ActorRef) -> None:
        """
        Publish the twin with a given descriptor.
        Raises ConflictError if the twin is already published at the same version.
        """
        if self.lifecycle == TwinLifecycleState.PUBLISHED:
            raise ConflictError(
                f"TwinAsset {self.id} is already published at version {self.version}",
                {"twin_id": str(self.id), "version": str(self.version)},
            )
        self.descriptor = descriptor
        self.lifecycle = TwinLifecycleState.PUBLISHED
        self.published_at = datetime.now(timezone.utc)

    def deprecate(self) -> None:
        """Mark the twin as deprecated."""
        self.lifecycle = TwinLifecycleState.DEPRECATED

    def withdraw(self) -> None:
        """Mark the twin as withdrawn."""
        self.lifecycle = TwinLifecycleState.WITHDRAWN

    def update_descriptor(self, descriptor: TwinDescriptor, actor: ActorRef) -> None:
        """Replace the descriptor and bump the minor version."""
        self.descriptor = descriptor
        self.version = self.version.bump_minor()
