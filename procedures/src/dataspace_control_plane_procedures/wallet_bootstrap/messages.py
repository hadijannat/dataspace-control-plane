from __future__ import annotations

from dataclasses import dataclass


# ── Signals ──────────────────────────────────────────────────────────────────

@dataclass
class CredentialIssuanceCallback:
    """Async callback from issuer once credential has been issued."""
    event_id: str
    credential_id: str
    issuer_ref: str


@dataclass
class ReissueRequested:
    """Request that a credential be re-issued."""
    event_id: str
    credential_type: str
    reason: str


# ── Update payloads ───────────────────────────────────────────────────────────

@dataclass
class PauseWallet:
    reviewer_id: str


@dataclass
class PauseResult:
    accepted: bool


@dataclass
class ResumeWallet:
    reviewer_id: str
    notes: str = ""


@dataclass
class ResumeResult:
    accepted: bool
