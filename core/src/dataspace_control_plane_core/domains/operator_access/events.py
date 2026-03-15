from __future__ import annotations
from dataclasses import dataclass
from dataspace_control_plane_core.domains._shared.events import DomainEvent


@dataclass(frozen=True)
class RoleGranted(DomainEvent, event_type="operator_access.RoleGranted"):
    subject: str = ""
    role_name: str = ""
    scope_resource: str = ""


@dataclass(frozen=True)
class GrantRevoked(DomainEvent, event_type="operator_access.GrantRevoked"):
    grant_id: str = ""
    subject: str = ""
