from __future__ import annotations
from dataclasses import dataclass

from dataspace_control_plane_core.domains._shared.events import DomainEvent
from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId


@dataclass(frozen=True)
class LegalEntityRegistered(DomainEvent, event_type="tenant_topology.LegalEntityRegistered"):
    legal_entity_id: LegalEntityId = None  # type: ignore[assignment]
    display_name: str = ""


@dataclass(frozen=True)
class LegalEntityActivated(DomainEvent, event_type="tenant_topology.LegalEntityActivated"):
    legal_entity_id: LegalEntityId = None  # type: ignore[assignment]


@dataclass(frozen=True)
class ExternalIdentifierAdded(DomainEvent, event_type="tenant_topology.ExternalIdentifierAdded"):
    legal_entity_id: LegalEntityId = None  # type: ignore[assignment]
    scheme: str = ""
    value: str = ""


@dataclass(frozen=True)
class EnvironmentRegistered(DomainEvent, event_type="tenant_topology.EnvironmentRegistered"):
    legal_entity_id: LegalEntityId = None  # type: ignore[assignment]
    environment_id: str = ""
