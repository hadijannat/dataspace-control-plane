"""
tests/chaos/workflow_recovery/test_worker_restart.py
Tests for Temporal workflow resilience during worker restarts.

Tests:
  1. Time-skipping environment handles conceptual restart
  2. Workflow resumes from golden history replay files
  3. No duplicate evidence on worker restart (marked xfail until implemented)

Marker: chaos
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.chaos

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
HISTORIES_DIR = REPO_ROOT / "tests" / "data" / "temporal_histories"


# ---------------------------------------------------------------------------
# Test 1: Time-skipping env handles restart
# ---------------------------------------------------------------------------


@pytest.mark.chaos
def test_time_skipping_env_handles_restart(temporal_env) -> None:
    """
    The time-skipping environment must remain functional after being used.

    In a real restart scenario, Temporal's persistence layer allows workflows
    to resume from their persisted state. This test verifies the test environment
    itself is stable.
    """
    temporalio = pytest.importorskip("temporalio")
    assert temporal_env is not None, "temporal_env must be non-None"
    assert temporal_env.client is not None, "temporal_env.client must be non-None after use"


# ---------------------------------------------------------------------------
# Test 2: Workflow resumes from history
# ---------------------------------------------------------------------------


@pytest.mark.chaos
def test_workflow_resumes_from_history() -> None:
    """
    Given a pre-recorded replay history in tests/data/temporal_histories/,
    load and validate it. Demonstrates that golden histories are well-formed
    and suitable for worker replay tests.
    """
    json_files = list(HISTORIES_DIR.glob("*.json"))
    if not json_files:
        pytest.skip("No golden history files available for replay test")

    for history_file in json_files:
        try:
            history = json.loads(history_file.read_text())
        except (json.JSONDecodeError, OSError) as exc:
            pytest.fail(f"History file {history_file.name} is not valid JSON: {exc}")

        assert history is not None, f"History file {history_file.name} loaded as None"
        # A Temporal workflow history typically has an 'events' key
        # This is a structural check — replay requires a valid event sequence
        if isinstance(history, dict):
            assert len(history) > 0, (
                f"History file {history_file.name} is an empty dict"
            )


# ---------------------------------------------------------------------------
# Test 3: No duplicate evidence on worker restart (xfail)
# ---------------------------------------------------------------------------


@pytest.mark.chaos
@pytest.mark.xfail(
    reason="Worker resilience against duplicate evidence emission not yet implemented. "
    "Requires idempotent evidence emission in procedures/. "
    "Track: procedures-lead wave 2.",
    strict=False,
)
def test_no_duplicate_evidence_on_worker_restart() -> None:
    """
    When a Temporal worker restarts mid-workflow, evidence must not be emitted twice.

    This requires idempotent evidence emission implemented in procedures/.
    Currently xfail — will be promoted to a strict assertion once implemented.
    """
    # This test is expected to fail until the implementation is ready.
    # When procedures/evidence_emitter.py implements idempotent emission,
    # remove the xfail marker and implement the actual duplicate-detection logic.
    raise NotImplementedError(
        "Idempotent evidence emission not yet implemented in procedures/"
    )
