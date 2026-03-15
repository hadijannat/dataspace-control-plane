from __future__ import annotations
from dataspace_control_plane_core.domains._shared.ids import AggregateId
from dataspace_control_plane_core.domains._shared.time import Clock, UtcClock
from .commands import (
    InitiateOnboardingCommand,
    AdvancePhaseCommand,
    CompleteOnboardingCommand,
)
from .events import (
    OnboardingInitiated,
    OnboardingPhaseStarted,
    OnboardingCompleted,
)
from .model.aggregates import OnboardingCase
from .model.enums import OnboardingPhase, OnboardingStatus
from .model.invariants import require_not_completed
from .ports import OnboardingCaseRepository


class OnboardingService:
    def __init__(self, repo: OnboardingCaseRepository, clock: Clock = UtcClock()) -> None:
        self._repo = repo
        self._clock = clock

    async def initiate(self, cmd: InitiateOnboardingCommand) -> OnboardingCase:
        """Create a new OnboardingCase and persist it."""
        case = OnboardingCase(
            id=AggregateId.generate(),
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
            request=cmd.request,
            phase=OnboardingPhase.IDENTITY_REGISTRATION,
            status=OnboardingStatus.PENDING,
        )
        case._raise_event(OnboardingInitiated(
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
            bpnl=cmd.request.bpnl,
        ))
        await self._repo.save(case, expected_version=0)
        return case

    async def advance_phase(self, cmd: AdvancePhaseCommand) -> OnboardingCase:
        """Advance the onboarding case to the next phase."""
        case = await self._repo.get(cmd.tenant_id, cmd.legal_entity_id)
        require_not_completed(case)
        case.start_phase(cmd.phase)
        case._raise_event(OnboardingPhaseStarted(
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
            phase=cmd.phase,
        ))
        await self._repo.save(case, expected_version=case.version)
        return case

    async def complete(self, cmd: CompleteOnboardingCommand) -> OnboardingCase:
        """Mark the onboarding case as successfully completed."""
        case = await self._repo.get(cmd.tenant_id, cmd.legal_entity_id)
        require_not_completed(case)
        case.complete()
        case._raise_event(OnboardingCompleted(
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
        ))
        await self._repo.save(case, expected_version=case.version)
        return case
