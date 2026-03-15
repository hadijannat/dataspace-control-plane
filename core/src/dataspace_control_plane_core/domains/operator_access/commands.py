from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from .model.value_objects import Scope


@dataclass(frozen=True)
class GrantRoleCommand:
    subject: str
    role_name: str
    scope: Scope
    granted_by: ActorRef
    expires_at: datetime | None
    correlation: CorrelationContext


@dataclass(frozen=True)
class RevokeGrantCommand:
    grant_id: str
    revoked_by: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class CheckAuthorizationCommand:
    principal: "OperatorPrincipal"  # noqa: F821
    action: str
    scope: Scope
    correlation: CorrelationContext
