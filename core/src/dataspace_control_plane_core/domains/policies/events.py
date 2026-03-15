from __future__ import annotations
from dataclasses import dataclass
from dataspace_control_plane_core.domains._shared.events import DomainEvent


@dataclass(frozen=True)
class PolicyTemplateCreated(DomainEvent, event_type="policies.PolicyTemplateCreated"):
    policy_id: str = ""
    name: str = ""
    has_parse_losses: bool = False

@dataclass(frozen=True)
class PolicyTemplateActivated(DomainEvent, event_type="policies.PolicyTemplateActivated"):
    policy_id: str = ""

@dataclass(frozen=True)
class PolicyEvaluated(DomainEvent, event_type="policies.PolicyEvaluated"):
    policy_id: str = ""
    allowed: bool = False
