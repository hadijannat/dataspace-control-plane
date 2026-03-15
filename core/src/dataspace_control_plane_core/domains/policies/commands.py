from __future__ import annotations
from dataclasses import dataclass
from dataspace_control_plane_core.domains._shared.ids import TenantId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from dataspace_control_plane_core.canonical_models.policy import CanonicalPolicy


@dataclass(frozen=True)
class CreatePolicyTemplateCommand:
    tenant_id: TenantId
    name: str
    description: str | None
    canonical_policy: CanonicalPolicy
    actor: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class ActivatePolicyTemplateCommand:
    tenant_id: TenantId
    policy_id: str
    actor: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class EvaluatePolicyCommand:
    policy_id: str
    subject: str
    action: str
    resource: str
    context: dict
    correlation: CorrelationContext
