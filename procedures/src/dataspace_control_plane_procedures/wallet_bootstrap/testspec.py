"""Test scenario specifications for WalletBootstrapWorkflow.

Each entry describes a named scenario, its key preconditions, and the expected
outcome. These drive unit-replay tests and integration test fixtures; actual
test implementations live in tests/.
"""
from __future__ import annotations

SCENARIOS: list[dict] = [
    {
        "name": "happy_path",
        "description": (
            "All activities succeed in sequence. Credential issuance callback arrives "
            "before the wait_condition timeout. Wallet is bound to connector."
        ),
        "preconditions": {
            "wallet_service": "available",
            "did_registrar": "available",
            "issuer": "available",
            "connector": "available",
        },
        "expected_outcome": {
            "wallet_state": "bound_to_connector",
            "status": "completed",
            "is_bound": True,
        },
    },
    {
        "name": "credential_issuance_via_async_callback",
        "description": (
            "credential_request_from_issuer returns a request_ref; the workflow "
            "waits on CredentialIssuanceCallback signal before proceeding to "
            "verify_credential_presentation."
        ),
        "preconditions": {
            "issuer": "async_callback_mode",
        },
        "expected_outcome": {
            "wallet_state": "bound_to_connector",
            "credential_count": 1,
        },
    },
    {
        "name": "manual_review_on_lossy_credential",
        "description": (
            "Credential verification reveals a lossy/degraded credential. Workflow "
            "enters manual_review state. Operator resumes with ResumeWallet update. "
            "Reissue is then triggered."
        ),
        "preconditions": {
            "verify_credential_presentation": "lossy_credential",
        },
        "expected_outcome": {
            "manual_review_entered": True,
            "resumed_after_review": True,
        },
    },
    {
        "name": "reissue_signal",
        "description": (
            "ReissueRequested signal is delivered after credential is bound. "
            "Workflow queues a reissue, triggers manual review if required, "
            "and transitions back to credential_request_sent state."
        ),
        "preconditions": {
            "wallet_state_at_signal": "bound_to_connector",
        },
        "expected_outcome": {
            "reissue_queued": True,
        },
    },
    {
        "name": "pause_and_resume",
        "description": (
            "PauseWallet update is accepted while wallet is in a non-terminal state. "
            "ResumeWallet update is accepted while paused. Workflow continues normally."
        ),
        "preconditions": {
            "pause_at": "credential_request_sent",
        },
        "expected_outcome": {
            "paused": True,
            "resumed": True,
            "status": "completed",
        },
    },
    {
        "name": "did_registration_fails_compensates",
        "description": (
            "register_did activity raises DidRegistrationError after max retries. "
            "Compensation runs decommission_wallet to clean up the already-created "
            "wallet. Workflow terminates with failure."
        ),
        "preconditions": {
            "did_registrar": "always_fails",
        },
        "expected_outcome": {
            "compensation_ran": True,
            "decommission_wallet_called": True,
            "status": "failed",
        },
    },
]
