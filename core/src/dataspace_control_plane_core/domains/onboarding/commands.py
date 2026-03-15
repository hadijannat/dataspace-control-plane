from __future__ import annotations
from dataclasses import dataclass
from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId, WorkflowId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from .model.enums import OnboardingPhase
from .model.value_objects import OnboardingRequest, PhaseResult


@dataclass(frozen=True)
class InitiateOnboardingCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    request: OnboardingRequest
    actor: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class AdvancePhaseCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    phase: OnboardingPhase
    actor: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class RecordCheckpointCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    result: PhaseResult
    actor: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class CompleteOnboardingCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    actor: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class CancelOnboardingCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    reason: str
    actor: ActorRef
    correlation: CorrelationContext
