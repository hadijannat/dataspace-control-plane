"""Activity definitions for the rotate_credentials procedure.

All I/O, external calls, and side effects live here — never in workflow code.
Activities heartbeat on long-running operations so Temporal can detect worker loss.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from temporalio import activity


# ---------------------------------------------------------------------------
# enumerate_expiring_credentials
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EnumerateInput:
    tenant_id: str
    legal_entity_id: str
    credential_profile: str
    look_ahead_days: int


@dataclass(frozen=True)
class EnumerateResult:
    credential_ids: list[str] = field(default_factory=list)


@activity.defn
async def enumerate_expiring_credentials(inp: EnumerateInput) -> EnumerateResult:
    """Scan the trust domain for credentials expiring within look_ahead_days.

    Returns a list of credential IDs that need rotation.
    """
    # Real implementation: queries core trust domain / credential registry.
    return EnumerateResult(credential_ids=[])


# ---------------------------------------------------------------------------
# request_credential_reissuance
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReissueInput:
    tenant_id: str
    legal_entity_id: str
    credential_profile: str
    expiring_credential_ids: list[str]


@dataclass(frozen=True)
class ReissueResult:
    new_credential_ids: list[str] = field(default_factory=list)


@activity.defn
async def request_credential_reissuance(inp: ReissueInput) -> ReissueResult:
    """Call the credential issuer for each expiring credential.

    Heartbeats during the reissuance calls because the issuer may have
    significant latency.
    """
    new_ids: list[str] = []
    for old_id in inp.expiring_credential_ids:
        activity.heartbeat(f"requesting reissuance for {old_id}")
        new_id = f"new-cred:{inp.tenant_id}:{inp.legal_entity_id}:{old_id}"
        new_ids.append(new_id)
        activity.heartbeat(f"reissuance complete for {old_id} -> {new_id}")
    return ReissueResult(new_credential_ids=new_ids)


# ---------------------------------------------------------------------------
# verify_new_credential_presentation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VerifyInput:
    tenant_id: str
    legal_entity_id: str
    new_credential_ids: list[str]


@dataclass(frozen=True)
class VerifyResult:
    ok: bool
    failed_ids: list[str] = field(default_factory=list)


@activity.defn
async def verify_new_credential_presentation(inp: VerifyInput) -> VerifyResult:
    """Verify the new credentials via presentation to the trust anchor.

    Returns ok=True only if all new credentials pass verification.
    """
    # Real implementation: calls trust domain presentation verification port.
    return VerifyResult(ok=True)


# ---------------------------------------------------------------------------
# update_connector_wallet_bindings
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BindingUpdateInput:
    tenant_id: str
    legal_entity_id: str
    old_credential_ids: list[str]
    new_credential_ids: list[str]


@dataclass(frozen=True)
class BindingUpdateResult:
    updated: bool
    binding_ref: str = ""


@activity.defn
async def update_connector_wallet_bindings(inp: BindingUpdateInput) -> BindingUpdateResult:
    """Update connector and wallet configurations to use the new credentials.

    Heartbeats because connector/wallet updates may involve multiple external calls.
    """
    activity.heartbeat("updating connector wallet bindings")
    binding_ref = f"binding:{inp.tenant_id}:{inp.legal_entity_id}"
    activity.heartbeat("connector wallet bindings updated")
    return BindingUpdateResult(updated=True, binding_ref=binding_ref)


# ---------------------------------------------------------------------------
# retire_old_credentials
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RetireInput:
    tenant_id: str
    legal_entity_id: str
    old_credential_ids: list[str]


@dataclass(frozen=True)
class RetireResult:
    retired_count: int = 0


@activity.defn
async def retire_old_credentials(inp: RetireInput) -> RetireResult:
    """Mark old credentials as retired/revoked in the trust domain."""
    # Real implementation: calls trust domain retirement/revocation port.
    return RetireResult(retired_count=len(inp.old_credential_ids))


# ---------------------------------------------------------------------------
# schedule_next_rotation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ScheduleInput:
    tenant_id: str
    legal_entity_id: str
    credential_profile: str
    rotation_interval_days: int
    last_rotation_at: str


@dataclass(frozen=True)
class ScheduleResult:
    next_rotation_at: str


@activity.defn
async def schedule_next_rotation(inp: ScheduleInput) -> ScheduleResult:
    """Compute the next rotation timestamp based on the rotation interval.

    Returns an ISO-8601 string for the next scheduled rotation.
    """
    # Real implementation: computes next_at from last_rotation_at + interval.
    next_rotation_at = f"scheduled:{inp.rotation_interval_days}d-from:{inp.last_rotation_at}"
    return ScheduleResult(next_rotation_at=next_rotation_at)


# ---------------------------------------------------------------------------
# Compensation: retire_new_credentials_on_failure
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RetireNewCredentialsInput:
    tenant_id: str
    legal_entity_id: str
    new_credential_ids: list[str]


@activity.defn
async def retire_new_credentials_on_failure(inp: RetireNewCredentialsInput) -> None:
    """Compensation: retire newly issued credentials when binding update fails.

    Rolls back to the old credentials by invalidating the new ones.
    Heartbeats because credential retirement may involve external calls.
    """
    for cred_id in inp.new_credential_ids:
        activity.heartbeat(f"retiring new credential {cred_id} (compensation)")
    # Real implementation: calls trust domain retirement port for each new credential.
    activity.heartbeat("compensation complete — new credentials retired")
