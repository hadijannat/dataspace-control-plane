from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone

from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId, WorkflowId
from dataspace_control_plane_core.domains._shared.errors import ValidationError
from .enums import OnboardingPhase, OnboardingStatus
from .value_objects import OnboardingRequest, PhaseResult, OnboardingCheckpoint


@dataclass
class OnboardingCase(AggregateRoot):
    """
    Aggregate root for a company onboarding lifecycle.
    Tracks phase progression, checkpoints, and final status.
    """
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId(""))
    request: OnboardingRequest | None = None
    phase: OnboardingPhase = OnboardingPhase.IDENTITY_REGISTRATION
    status: OnboardingStatus = OnboardingStatus.PENDING
    checkpoints: list[OnboardingCheckpoint] = field(default_factory=list)
    workflow_id: WorkflowId | None = None

    def start_phase(self, phase: OnboardingPhase) -> None:
        """Advance to the given phase and mark as in-progress."""
        self.phase = phase
        self.status = OnboardingStatus.IN_PROGRESS

    def record_checkpoint(self, result: PhaseResult) -> None:
        """Append a checkpoint for the completed phase step."""
        checkpoint = OnboardingCheckpoint(
            phase=result.phase,
            result=result,
            occurred_at=datetime.now(timezone.utc),
        )
        self.checkpoints.append(checkpoint)

    def complete(self) -> None:
        """Mark the onboarding case as fully completed."""
        self.phase = OnboardingPhase.COMPLETED
        self.status = OnboardingStatus.COMPLETED

    def fail(self, reason: str) -> None:
        """Mark the onboarding case as failed."""
        self.phase = OnboardingPhase.FAILED
        self.status = OnboardingStatus.FAILED
