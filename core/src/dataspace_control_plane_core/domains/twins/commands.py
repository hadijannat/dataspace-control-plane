"""Command objects for the twins domain."""
from __future__ import annotations
from dataclasses import dataclass, field

from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from .model.value_objects import TwinDescriptor
from .model.enums import TwinVisibility


@dataclass(frozen=True)
class RegisterTwinCommand:
    """Register a new twin asset skeleton (no descriptor yet)."""
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    global_asset_id: str
    visibility: TwinVisibility
    actor: ActorRef


@dataclass(frozen=True)
class PublishTwinCommand:
    """Publish an existing twin with a descriptor."""
    tenant_id: TenantId
    twin_id: AggregateId
    descriptor: TwinDescriptor
    actor: ActorRef


@dataclass(frozen=True)
class UpdateTwinDescriptorCommand:
    """Replace the descriptor of a published twin (bumps minor version)."""
    tenant_id: TenantId
    twin_id: AggregateId
    descriptor: TwinDescriptor
    actor: ActorRef


@dataclass(frozen=True)
class DeprecateTwinCommand:
    """Deprecate a twin."""
    tenant_id: TenantId
    twin_id: AggregateId
    actor: ActorRef


@dataclass(frozen=True)
class WithdrawTwinCommand:
    """Withdraw a twin from publication."""
    tenant_id: TenantId
    twin_id: AggregateId
    actor: ActorRef
