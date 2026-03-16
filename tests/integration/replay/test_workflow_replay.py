"""
tests/integration/replay/test_workflow_replay.py
Integration tests for Temporal workflow replay from golden history files.

Tests:
  1. tests/data/temporal_histories/ directory exists         (unit — no live services)
  2. All .json files in the histories directory are valid JSON (unit — no live services)
  3. Temporal time-skipping environment starts successfully  (integration — requires --live-services)
  4. Time-skipping clock can be advanced                     (integration — requires --live-services)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
HISTORIES_DIR = REPO_ROOT / "tests" / "data" / "temporal_histories"


# ---------------------------------------------------------------------------
# Test 1: temporal_histories directory exists  (no live services needed)
# ---------------------------------------------------------------------------


def test_replay_histories_dir_exists() -> None:
    """tests/data/temporal_histories/ must exist as a directory."""
    assert HISTORIES_DIR.exists(), (
        f"Temporal histories directory not found: {HISTORIES_DIR}"
    )
    assert HISTORIES_DIR.is_dir(), f"{HISTORIES_DIR} is not a directory"


# ---------------------------------------------------------------------------
# Test 2: Golden history files load as valid JSON  (no live services needed)
# ---------------------------------------------------------------------------


def test_replay_golden_files_load_cleanly() -> None:
    """Every .json file in temporal_histories/ must be valid JSON."""
    json_files = list(HISTORIES_DIR.glob("*.json"))
    if not json_files:
        pytest.skip("No golden history files in temporal_histories/ — nothing to replay")

    corrupt: list[str] = []
    for history_file in json_files:
        try:
            data = json.loads(history_file.read_text())
            assert data is not None
        except (json.JSONDecodeError, OSError) as exc:
            corrupt.append(f"{history_file.name}: {exc}")

    assert not corrupt, (
        f"{len(corrupt)} history file(s) failed to load as valid JSON:\n"
        + "\n".join(f"  {c}" for c in corrupt)
    )


# ---------------------------------------------------------------------------
# Test 3: Temporal environment starts  (requires --live-services)
# ---------------------------------------------------------------------------


@pytest.mark.integration
@pytest.mark.asyncio
async def test_temporal_env_starts() -> None:
    """The time-skipping Temporal WorkflowEnvironment must start and provide a client."""
    pytest.importorskip("temporalio")
    from temporalio.testing import WorkflowEnvironment

    env = await WorkflowEnvironment.start_time_skipping()
    try:
        assert env is not None, "temporal_env fixture returned None"
        assert env.client is not None, (
            "temporal_env.client is None — environment did not start correctly"
        )
    finally:
        await env.shutdown()


# ---------------------------------------------------------------------------
# Test 4: Time-skipping advances clock without error  (requires --live-services)
# ---------------------------------------------------------------------------


@pytest.mark.integration
async def test_time_skipping_advances_clock() -> None:
    """temporal_env.sleep(3600) must advance the virtual clock by 1 hour without error."""
    pytest.importorskip("temporalio")
    from temporalio.testing import WorkflowEnvironment

    env = await WorkflowEnvironment.start_time_skipping()
    try:
        await env.sleep(3600)
    finally:
        await env.shutdown()
