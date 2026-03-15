from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from .enums import OnboardingPhase


@dataclass(frozen=True)
class OnboardingRequest:
    legal_entity_name: str
    bpnl: str
    jurisdiction: str
    contact_email: str
    connector_url: str


@dataclass(frozen=True)
class PhaseResult:
    phase: OnboardingPhase
    succeeded: bool
    detail: str
    completed_at: datetime


@dataclass(frozen=True)
class OnboardingCheckpoint:
    phase: OnboardingPhase
    result: PhaseResult
    occurred_at: datetime


@dataclass(frozen=True)
class Prerequisite:
    prerequisite_id: str
    description: str
    satisfied: bool = False


@dataclass(frozen=True)
class CapabilityCheck:
    name: str
    passed: bool
    detail: str = ""


@dataclass(frozen=True)
class OnboardingDecision:
    approved: bool
    rationale: str = ""


@dataclass(frozen=True)
class ReadinessReport:
    generated_at: datetime
    checks: tuple[CapabilityCheck, ...]
    decision: OnboardingDecision
