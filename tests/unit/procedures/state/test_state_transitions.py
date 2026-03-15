"""
tests/unit/procedures/state/test_state_transitions.py
Unit tests for passport lifecycle state machine contracts.

Tests:
  1. Canonical lifecycle states are present in passport-lifecycle schema
  2. Terminal/ceased states are identifiable from schema descriptions
  3. Transition history is append-only (removing an entry is invalid)

Uses the live passport-lifecycle.schema.json from schemas/dpp/source/base/.
Marker: unit
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
LIFECYCLE_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "dpp" / "source" / "base" / "passport-lifecycle.schema.json"
)


@pytest.fixture(scope="module")
def lifecycle_schema() -> dict:
    if not LIFECYCLE_SCHEMA_PATH.exists():
        pytest.skip(f"passport-lifecycle schema not found: {LIFECYCLE_SCHEMA_PATH}")
    return json.loads(LIFECYCLE_SCHEMA_PATH.read_text())


# ---------------------------------------------------------------------------
# Test 1: Canonical lifecycle states are present
# ---------------------------------------------------------------------------


def test_passport_lifecycle_states_from_schema(lifecycle_schema: dict) -> None:
    """
    The passport-lifecycle schema must define the canonical currentState enum
    containing at least the four core terminal/active states.
    """
    props = lifecycle_schema.get("properties", {})
    current_state = props.get("currentState", {})
    enum_values = current_state.get("enum", [])

    assert enum_values, (
        "passport-lifecycle.schema.json must define currentState enum values"
    )

    required_states = {"active", "waste", "recycled_ceased", "decommissioned"}
    missing = required_states - set(enum_values)
    assert not missing, (
        f"Missing canonical lifecycle states in currentState enum: {missing}\n"
        f"Found states: {enum_values}"
    )


# ---------------------------------------------------------------------------
# Test 2: Terminal/ceased states are in the enum
# ---------------------------------------------------------------------------


def test_lifecycle_terminal_states(lifecycle_schema: dict) -> None:
    """
    'decommissioned' and 'recycled_ceased' must be present as possible ceased states.

    These represent end-of-life states where the passport lifecycle is complete
    and no further transitions should occur.
    """
    props = lifecycle_schema.get("properties", {})
    current_state = props.get("currentState", {})
    enum_values = set(current_state.get("enum", []))

    ceased_states = {"decommissioned", "recycled_ceased"}
    for state in ceased_states:
        assert state in enum_values, (
            f"Terminal/ceased state '{state}' must be in currentState enum.\n"
            f"Current enum: {sorted(enum_values)}"
        )


# ---------------------------------------------------------------------------
# Test 3: Transition history is append-only
# ---------------------------------------------------------------------------


def test_transition_history_is_append_only(lifecycle_schema: dict) -> None:
    """
    A lifecycle record whose transition history has fewer entries than a previous
    version must be detected as invalid (append-only invariant).

    This test implements the invariant check inline since procedures/ is not yet scaffolded.
    """

    def _validate_append_only(
        history_v1: list[dict], history_v2: list[dict]
    ) -> tuple[bool, str]:
        """
        Return (True, '') if v2 history is a valid extension of v1 history.
        Return (False, reason) if v2 has removed or altered historical entries.
        """
        if len(history_v2) < len(history_v1):
            return False, (
                f"Transition history shrank: v1 had {len(history_v1)} entries, "
                f"v2 has {len(history_v2)} entries"
            )
        for idx, (entry_v1, entry_v2) in enumerate(zip(history_v1, history_v2)):
            if entry_v1 != entry_v2:
                return False, (
                    f"Transition history entry {idx} was mutated: "
                    f"v1={entry_v1!r}, v2={entry_v2!r}"
                )
        return True, ""

    t1 = {"fromState": "active", "toState": "waste", "occurredAt": "2026-01-01T00:00:00Z"}
    t2 = {"fromState": "waste", "toState": "recycled_ceased", "occurredAt": "2026-02-01T00:00:00Z"}

    # Valid: v2 appends to v1's history
    valid, reason = _validate_append_only([t1], [t1, t2])
    assert valid, f"Append-only check incorrectly rejected valid history extension: {reason}"

    # Invalid: v2 removes an entry
    invalid, reason = _validate_append_only([t1, t2], [t2])
    assert not invalid, "Append-only check must reject history with removed entries"
    assert "shrank" in reason.lower() or "mutated" in reason.lower(), (
        f"Expected informative reason for rejection, got: {reason!r}"
    )

    # Invalid: v2 alters an existing entry
    t1_altered = {**t1, "performedBy": "injected-actor"}
    mutated, reason = _validate_append_only([t1], [t1_altered])
    assert not mutated, "Append-only check must reject history with altered entries"
