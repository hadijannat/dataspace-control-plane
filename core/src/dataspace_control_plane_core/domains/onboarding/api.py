"""Public API surface for onboarding domain. Only import from here."""
from .model.enums import OnboardingPhase, OnboardingStatus
from .model.value_objects import (
    CapabilityCheck,
    OnboardingCheckpoint,
    OnboardingDecision,
    OnboardingRequest,
    PhaseResult,
    Prerequisite,
    ReadinessReport,
)
from .model.aggregates import OnboardingCase
from .model.invariants import require_not_completed
from .commands import (
    InitiateOnboardingCommand,
    AdvancePhaseCommand,
    RecordCheckpointCommand,
    CompleteOnboardingCommand,
    CancelOnboardingCommand,
)
from .events import (
    OnboardingInitiated,
    OnboardingPhaseStarted,
    OnboardingPhaseCompleted,
    OnboardingCompleted,
    OnboardingFailed,
)
from .errors import (
    OnboardingNotFoundError,
    OnboardingAlreadyCompletedError,
    OnboardingPhaseOrderViolationError,
)
from .ports import (
    ComplianceBaselinePort,
    ConnectorProvisioningPort,
    ConnectorReadinessPort,
    IdentityProvisioningPort,
    OnboardingCaseRepository,
    PolicyCatalogReadinessPort,
    TopologyLookupPort,
    TrustReadinessPort,
)
from .services import OnboardingService

__all__ = [
    "OnboardingPhase",
    "OnboardingStatus",
    "OnboardingRequest",
    "PhaseResult", "OnboardingCheckpoint",
    "Prerequisite", "CapabilityCheck", "OnboardingDecision", "ReadinessReport",
    "OnboardingCase",
    "require_not_completed",
    "InitiateOnboardingCommand",
    "AdvancePhaseCommand",
    "RecordCheckpointCommand",
    "CompleteOnboardingCommand",
    "CancelOnboardingCommand",
    "OnboardingInitiated",
    "OnboardingPhaseStarted",
    "OnboardingPhaseCompleted",
    "OnboardingCompleted",
    "OnboardingFailed",
    "OnboardingNotFoundError",
    "OnboardingAlreadyCompletedError",
    "OnboardingPhaseOrderViolationError",
    "OnboardingCaseRepository",
    "IdentityProvisioningPort",
    "ConnectorProvisioningPort",
    "TopologyLookupPort",
    "TrustReadinessPort",
    "ConnectorReadinessPort",
    "PolicyCatalogReadinessPort",
    "ComplianceBaselinePort",
    "OnboardingService",
]
