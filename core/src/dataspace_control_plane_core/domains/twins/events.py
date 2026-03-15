"""Domain events for the twins domain."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar

from dataspace_control_plane_core.domains._shared.events import DomainEvent
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId
from dataspace_control_plane_core.domains._shared.time import utc_now


@dataclass(frozen=True)
class TwinRegistered(DomainEvent):
    event_type: ClassVar[str] = "twins.registered"
    twin_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId("__unset__"))
    global_asset_id: str = ""


@dataclass(frozen=True)
class TwinPublished(DomainEvent):
    event_type: ClassVar[str] = "twins.published"
    twin_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))
    global_asset_id: str = ""
    version: str = ""
    published_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class TwinDescriptorUpdated(DomainEvent):
    event_type: ClassVar[str] = "twins.descriptor_updated"
    twin_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))
    new_version: str = ""


@dataclass(frozen=True)
class TwinDeprecated(DomainEvent):
    event_type: ClassVar[str] = "twins.deprecated"
    twin_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))


@dataclass(frozen=True)
class TwinWithdrawn(DomainEvent):
    event_type: ClassVar[str] = "twins.withdrawn"
    twin_id: AggregateId = field(default_factory=lambda: AggregateId.generate())
    tenant_id: TenantId = field(default_factory=lambda: TenantId("__unset__"))
