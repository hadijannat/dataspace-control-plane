"""Test scenario specifications for PublishAssetWorkflow."""
from __future__ import annotations

SCENARIOS: list[dict] = [
    {
        "name": "happy_path",
        "description": (
            "All activities succeed in sequence. Policy is lossless. Asset offer is "
            "published and is visible to consumers. Evidence is recorded."
        ),
        "preconditions": {
            "source": "available",
            "policy_compile": "lossless",
            "catalog": "available",
            "visibility_check": "visible",
        },
        "expected_outcome": {
            "phase": "evidence_recorded",
            "status": "completed",
            "is_visible": True,
        },
    },
    {
        "name": "lossy_policy_triggers_manual_review",
        "description": (
            "compile_policy returns lossy=True. Workflow pauses in manual review. "
            "Operator approves via ForceRepublish update. Publication proceeds."
        ),
        "preconditions": {
            "policy_compile": "lossy",
        },
        "expected_outcome": {
            "manual_review_entered": True,
            "force_republish_accepted": True,
            "status": "completed",
        },
    },
    {
        "name": "force_republish_update",
        "description": (
            "Asset was previously published (phase=evidence_recorded). "
            "ForceRepublish update re-triggers the publish step."
        ),
        "preconditions": {
            "force_republish": True,
        },
        "expected_outcome": {
            "republished": True,
            "status": "completed",
        },
    },
    {
        "name": "source_not_ready_retried",
        "description": (
            "validate_source_readiness returns ok=False on first attempts. "
            "Activity is retried until source is ready."
        ),
        "preconditions": {
            "source_readiness_attempts_before_ok": 3,
        },
        "expected_outcome": {
            "status": "completed",
        },
    },
    {
        "name": "visibility_check_fails_retried",
        "description": (
            "run_consumer_visibility_check returns visible=False on first attempts. "
            "Activity is retried until visibility is confirmed."
        ),
        "preconditions": {
            "visibility_check_attempts_before_ok": 2,
        },
        "expected_outcome": {
            "is_visible": True,
            "status": "completed",
        },
    },
    {
        "name": "compensation_on_error",
        "description": (
            "publish_asset_offer raises AssetPublishError after the snapshot and "
            "policy are compiled. Compensation retracts any partial offer and "
            "workflow terminates with failure."
        ),
        "preconditions": {
            "publish_asset_offer": "always_fails",
        },
        "expected_outcome": {
            "compensation_ran": True,
            "status": "failed",
        },
    },
]
