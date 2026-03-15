"""Command objects for the schema_mapping domain."""
from __future__ import annotations
from dataclasses import dataclass

from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from .model.enums import MappingDirection
from .model.value_objects import MappingRule


@dataclass(frozen=True)
class CreateMappingCommand:
    """Create a new schema mapping in DRAFT state."""
    tenant_id: TenantId
    source_schema_id: str
    target_schema_id: str
    direction: MappingDirection
    actor: ActorRef


@dataclass(frozen=True)
class ActivateMappingCommand:
    """Activate an existing schema mapping."""
    tenant_id: TenantId
    mapping_id: AggregateId
    actor: ActorRef


@dataclass(frozen=True)
class AddMappingRuleCommand:
    """Add a rule to an existing schema mapping."""
    tenant_id: TenantId
    mapping_id: AggregateId
    rule: MappingRule
    actor: ActorRef


@dataclass(frozen=True)
class RemoveMappingRuleCommand:
    """Remove a rule by source_path from an existing schema mapping."""
    tenant_id: TenantId
    mapping_id: AggregateId
    source_path: str
    actor: ActorRef


@dataclass(frozen=True)
class DeprecateMappingCommand:
    """Deprecate an existing schema mapping."""
    tenant_id: TenantId
    mapping_id: AggregateId
    actor: ActorRef
