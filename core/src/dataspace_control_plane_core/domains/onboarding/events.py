from __future__ import annotations
from dataclasses import dataclass
from typing import ClassVar
from dataspace_control_plane_core.domains._shared.events import DomainEvent
from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId
from .model.enums import OnboardingPhase, OnboardingStatus


@dataclass(frozen=True)
class OnboardingInitiated(DomainEvent, event_type="onboarding.OnboardingInitiated"):
    legal_entity_id: LegalEntityId = None  # type: ignore[assignment]
    bpnl: str = ""


@dataclass(frozen=True)
class OnboardingPhaseStarted(DomainEvent, event_type="onboarding.OnboardingPhaseStarted"):
    legal_entity_id: LegalEntityId = None  # type: ignore[assignment]
    phase: OnboardingPhase = OnboardingPhase.IDENTITY_REGISTRATION


@dataclass(frozen=True)
class OnboardingPhaseCompleted(DomainEvent, event_type="onboarding.OnboardingPhaseCompleted"):
    legal_entity_id: LegalEntityId = None  # type: ignore[assignment]
    phase: OnboardingPhase = OnboardingPhase.IDENTITY_REGISTRATION
    succeeded: bool = True


@dataclass(frozen=True)
class OnboardingCompleted(DomainEvent, event_type="onboarding.OnboardingCompleted"):
    legal_entity_id: LegalEntityId = None  # type: ignore[assignment]


@dataclass(frozen=True)
class OnboardingFailed(DomainEvent, event_type="onboarding.OnboardingFailed"):
    legal_entity_id: LegalEntityId = None  # type: ignore[assignment]
    reason: str = ""
