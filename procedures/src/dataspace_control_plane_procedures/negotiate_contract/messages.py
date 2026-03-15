from __future__ import annotations

from dataclasses import dataclass, field


# ── Signals ───────────────────────────────────────────────────────────────────

@dataclass
class CounterpartyAccepted:
    """Async protocol event from connector webhook — counterparty accepted our offer."""
    event_id: str
    negotiation_ref: str


@dataclass
class CounterpartyRejected:
    """Async protocol event from connector webhook — counterparty rejected."""
    event_id: str
    reason: str


@dataclass
class CounterpartyCounteroffer:
    """Async protocol event from connector webhook — counterparty sent a counteroffer."""
    event_id: str
    new_offer_id: str
    policy_id: str


@dataclass
class NegotiationExpired:
    """Timeout signal from external scheduler."""
    event_id: str


# ── Update payloads ───────────────────────────────────────────────────────────

@dataclass
class AcceptCounteroffer:
    """Human reviewer accepts the pending counteroffer."""
    reviewer_id: str
    new_offer_id: str


@dataclass
class CounterOfferResult:
    accepted: bool


@dataclass
class RejectNegotiation:
    """Human reviewer rejects the negotiation entirely."""
    reviewer_id: str
    reason: str


@dataclass
class RejectionResult:
    accepted: bool
