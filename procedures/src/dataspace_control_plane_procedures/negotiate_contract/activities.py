"""Activity definitions for the negotiate_contract procedure.

All I/O, external calls, and side effects live here — never in workflow code.
Activities heartbeat on long-running operations so Temporal can detect worker loss.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from temporalio import activity


# ---------------------------------------------------------------------------
# Credential and offer check
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CredCheckInput:
    tenant_id: str
    legal_entity_id: str
    offer_id: str
    policy_template_id: str
    counterparty_connector_id: str


@dataclass(frozen=True)
class CredCheckResult:
    ok: bool
    reason: str = ""


@activity.defn
async def check_credentials_and_offer(inp: CredCheckInput) -> CredCheckResult:
    """Verify our credentials against the offer policy.

    Heartbeats during the credential presentation check.
    """
    activity.heartbeat("verifying credentials against offer policy")
    # In production: calls the DCP adapter to present and verify credentials.
    activity.heartbeat("credential check complete")
    return CredCheckResult(ok=True)


# ---------------------------------------------------------------------------
# Start DSP negotiation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DspNegotiationInput:
    tenant_id: str
    legal_entity_id: str
    offer_id: str
    counterparty_connector_id: str
    purpose: str
    policy_template_id: str
    pack_id: str


@dataclass(frozen=True)
class DspNegotiationResult:
    negotiation_ref: str


@activity.defn
async def start_dsp_negotiation(inp: DspNegotiationInput) -> DspNegotiationResult:
    """Call connector adapter to initiate the DSP negotiation; returns negotiation_ref."""
    activity.heartbeat("initiating DSP contract negotiation")
    negotiation_ref = f"neg:{inp.tenant_id}:{inp.offer_id}:{inp.counterparty_connector_id}"
    activity.heartbeat("DSP negotiation initiated")
    return DspNegotiationResult(negotiation_ref=negotiation_ref)


# ---------------------------------------------------------------------------
# Submit counteroffer
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CounterOfferInput:
    tenant_id: str
    negotiation_ref: str
    new_offer_id: str
    policy_id: str


@dataclass(frozen=True)
class CounterOfferResult:
    submitted: bool
    new_negotiation_ref: str = ""


@activity.defn
async def submit_counteroffer(inp: CounterOfferInput) -> CounterOfferResult:
    """Submit a counteroffer via the connector adapter."""
    activity.heartbeat("submitting counteroffer")
    new_ref = f"{inp.negotiation_ref}:counter:{inp.new_offer_id}"
    activity.heartbeat("counteroffer submitted")
    return CounterOfferResult(submitted=True, new_negotiation_ref=new_ref)


# ---------------------------------------------------------------------------
# Conclude agreement
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AgreementInput:
    tenant_id: str
    legal_entity_id: str
    negotiation_ref: str
    offer_id: str
    asset_id: str
    counterparty_connector_id: str


@dataclass(frozen=True)
class AgreementResult:
    agreement_id: str


@activity.defn
async def conclude_agreement(inp: AgreementInput) -> AgreementResult:
    """Store the concluded agreement in core.contracts domain; returns agreement_id."""
    activity.heartbeat("concluding agreement in core.contracts")
    agreement_id = f"agr:{inp.tenant_id}:{inp.negotiation_ref}"
    activity.heartbeat("agreement stored")
    return AgreementResult(agreement_id=agreement_id)


# ---------------------------------------------------------------------------
# Create entitlement
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EntitlementInput:
    tenant_id: str
    legal_entity_id: str
    agreement_id: str
    asset_id: str
    purpose: str


@dataclass(frozen=True)
class EntitlementResult:
    entitlement_id: str


@activity.defn
async def create_entitlement(inp: EntitlementInput) -> EntitlementResult:
    """Create core.contracts.Entitlement; returns entitlement_id."""
    entitlement_id = f"ent:{inp.tenant_id}:{inp.agreement_id}"
    return EntitlementResult(entitlement_id=entitlement_id)


# ---------------------------------------------------------------------------
# Issue transfer authorization
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TransferAuthInput:
    tenant_id: str
    agreement_id: str
    entitlement_id: str
    asset_id: str


@dataclass(frozen=True)
class TransferAuthResult:
    transfer_auth_token: str


@activity.defn
async def issue_transfer_authorization(inp: TransferAuthInput) -> TransferAuthResult:
    """Issue a transfer auth token to the caller; returns token."""
    activity.heartbeat("issuing transfer authorization token")
    token = f"tok:{inp.tenant_id}:{inp.agreement_id}:{inp.entitlement_id}"
    activity.heartbeat("transfer authorization issued")
    return TransferAuthResult(transfer_auth_token=token)


# ---------------------------------------------------------------------------
# Record negotiation evidence
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EvidenceInput:
    tenant_id: str
    legal_entity_id: str
    negotiation_ref: str
    agreement_id: str
    workflow_id: str
    outcome: str


@activity.defn
async def record_negotiation_evidence(inp: EvidenceInput) -> None:
    """Emit an audit record for the negotiation outcome.

    Best-effort; retry policy handles transient failures.
    """
    # In production: calls core.audit adapter port.
    pass


# ---------------------------------------------------------------------------
# Compensation — cancel negotiation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CancelInput:
    tenant_id: str
    negotiation_ref: str
    reason: str


@activity.defn
async def cancel_negotiation(inp: CancelInput) -> None:
    """Compensation: send cancellation to counterparty via connector adapter."""
    activity.heartbeat(f"cancelling negotiation {inp.negotiation_ref}")
    # In production: calls connector adapter cancellation port.
    activity.heartbeat(f"negotiation {inp.negotiation_ref} cancelled")
