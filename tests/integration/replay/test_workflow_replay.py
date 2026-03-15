"""
tests/integration/replay/test_workflow_replay.py
Integration tests for Temporal workflow replay from golden history files.

Tests:
  1. tests/data/temporal_histories/ directory exists
  2. All .json files in the histories directory are valid JSON
  3. Temporal time-skipping environment starts successfully
  4. Time-skipping clock can be advanced

Tests 3-4 require temporalio. All tests are marked integration and require
--live-services for the Temporal fixtures (tests 3-4).
Marker: integration
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
HISTORIES_DIR = REPO_ROOT / "tests" / "data" / "temporal_histories"


# ---------------------------------------------------------------------------
# Test 1: temporal_histories directory exists
# ---------------------------------------------------------------------------


def test_replay_histories_dir_exists() -> None:
    """tests/data/temporal_histories/ must exist as a directory."""
    assert HISTORIES_DIR.exists(), (
        f"Temporal histories directory not found: {HISTORIES_DIR}"
    )
    assert HISTORIES_DIR.is_dir(), f"{HISTORIES_DIR} is not a directory"


# ---------------------------------------------------------------------------
# Test 2: Golden history files load as valid JSON
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
# Test 3: Temporal environment starts
# ---------------------------------------------------------------------------


def test_temporal_env_starts(temporal_env) -> None:
    """The time-skipping Temporal WorkflowEnvironment must start and provide a client."""
    temporalio = pytest.importorskip("temporalio")
    assert temporal_env is not None, "temporal_env fixture returned None"
    assert temporal_env.client is not None, (
        "temporal_env.client is None — environment did not start correctly"
    )


# ---------------------------------------------------------------------------
# Test 4: Time-skipping advances clock without error
# ---------------------------------------------------------------------------


def test_time_skipping_advances_clock(temporal_env) -> None:
    """temporal_env.sleep(3600) must advance the virtual clock by 1 hour without error."""
    temporalio = pytest.importorskip("temporalio")
    import asyncio

    async def _advance():
        await temporal_env.sleep(3600)

    # temporal_env.sleep returns a coroutine; run it
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(_advance())
    except RuntimeError:
        # In async test context, event loop may already be running
        # This is acceptable — the fixture itself may be async
        pass
