from __future__ import annotations
from dataclasses import dataclass
from dataspace_control_plane_core.domains._shared.events import DomainEvent
from dataspace_control_plane_core.domains._shared.ids import TenantId


@dataclass(frozen=True)
class DidRegistered(DomainEvent, event_type="machine_trust.DidRegistered"):
    did_uri: str = ""

@dataclass(frozen=True)
class CredentialAdded(DomainEvent, event_type="machine_trust.CredentialAdded"):
    credential_id: str = ""
    credential_type: str = ""

@dataclass(frozen=True)
class CredentialRevoked(DomainEvent, event_type="machine_trust.CredentialRevoked"):
    credential_id: str = ""
    reason: str = ""
