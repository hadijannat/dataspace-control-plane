"""Domain events for the schema_mapping domain."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import ClassVar

from dataspace_control_plane_core.domains._shared.events import DomainEvent
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId


@dataclass(frozen=True)
class MappingCreated(DomainEvent):
    event_type: ClassVar[str] = "schema_mapping.created"
    mapping_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))
    source_schema_id: str = ""
    target_schema_id: str = ""


@dataclass(frozen=True)
class MappingActivated(DomainEvent):
    event_type: ClassVar[str] = "schema_mapping.activated"
    mapping_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))


@dataclass(frozen=True)
class MappingRuleAdded(DomainEvent):
    event_type: ClassVar[str] = "schema_mapping.rule_added"
    mapping_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))
    source_path: str = ""
    target_path: str = ""


@dataclass(frozen=True)
class MappingDeprecated(DomainEvent):
    event_type: ClassVar[str] = "schema_mapping.deprecated"
    mapping_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))
