"""Test scenario identifiers for rotate_credentials.

Used by tests/unit, tests/integration, and tests/chaos to select and
parametrize workflow replay scenarios without hardcoding string literals.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RotationScenarios:
    """Canonical scenario names for the rotate_credentials workflow test suite."""

    # Normal scheduled rotation: credentials are expiring, reissued, verified,
    # bindings updated, old credentials retired, next rotation scheduled.
    happy_path_scheduled: str = "happy_path_scheduled"

    # ForceRotate signal arrives mid-sleep; workflow wakes early and runs a cycle.
    force_rotate_signal: str = "force_rotate_signal"

    # PauseRotation update accepted; workflow waits; ResumeRotation update resumes it.
    pause_and_resume: str = "pause_and_resume"

    # verify_new_credential_presentation returns ok=False; compensation retires
    # newly issued credentials; workflow raises PresentationVerifyError.
    verification_fails_compensates: str = "verification_fails_compensates"

    # Duplicate ForceRotate signals with the same event_id are silently dropped
    # by the DedupeState; only one rotation cycle runs.
    duplicate_force_rotate_deduplicated: str = "duplicate_force_rotate_deduplicated"

    # After enough iterations the workflow calls continue_as_new, carrying
    # DedupeState, rotated_count, and last_rotation_at across the boundary.
    continue_as_new_carries_dedupe_state: str = "continue_as_new_carries_dedupe_state"

    # enumerate_expiring_credentials returns an empty list; the cycle is a no-op
    # and no reissuance or retirement activities are invoked.
    no_expiring_credentials_no_op: str = "no_expiring_credentials_no_op"


SCENARIOS = RotationScenarios()
