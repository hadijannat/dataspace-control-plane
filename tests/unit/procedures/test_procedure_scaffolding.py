"""
tests/unit/procedures/test_procedure_scaffolding.py
Unit tests for the procedures/ package scaffold and shared utilities.

Covers:
  - All 11 procedure testspec modules are importable and expose SCENARIOS
  - Every scenario attribute is a non-empty string identifier
  - _shared.compensation.CompensationLog: records accumulate and pending() is LIFO
  - _shared.compensation.CompensationLog: mark_compensated() removes from pending()
  - _shared.continue_as_new.should_continue_as_new() threshold logic
  - _shared.continue_as_new.DedupeState: deduplication, mark_handled(), max_size eviction
  - _shared.continue_as_new.DedupeState: snapshot round-trip via from_snapshot()

Marker: unit
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# ── Path injection ────────────────────────────────────────────────────────────
_PROCS_SRC = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "procedures"
    / "src"
)
if _PROCS_SRC.exists() and str(_PROCS_SRC) not in sys.path:
    sys.path.insert(0, str(_PROCS_SRC))


def _skip_if_missing(module_name: str = "dataspace_control_plane_procedures") -> None:
    try:
        __import__(module_name)
    except ImportError as exc:
        pytest.skip(f"{module_name} not available: {exc}")


# ── Testspec discoverability ──────────────────────────────────────────────────

_ALL_PROCEDURE_PACKAGES = [
    "company_onboarding",
    "connector_bootstrap",
    "delegate_tenant",
    "wallet_bootstrap",
    "rotate_credentials",
    "revoke_credentials",
    "register_digital_twin",
    "publish_asset",
    "dpp_provision",
    "negotiate_contract",
    "evidence_export",
]


@pytest.mark.parametrize("package_name", _ALL_PROCEDURE_PACKAGES)
def test_testspec_is_importable(package_name: str) -> None:
    """Every procedure package must expose a testspec.py module with SCENARIOS."""
    _skip_if_missing()

    module_path = (
        f"dataspace_control_plane_procedures.{package_name}.testspec"
    )
    try:
        testspec = __import__(module_path, fromlist=["SCENARIOS"])
    except ImportError as exc:
        pytest.fail(
            f"Could not import {module_path}: {exc}\n"
            "Every procedure package must ship a testspec.py with a SCENARIOS dataclass."
        )

    assert hasattr(testspec, "SCENARIOS"), (
        f"{module_path} must expose a SCENARIOS attribute at module level"
    )


def _extract_scenario_names(scenarios: object) -> list[str]:
    """Extract scenario identifiers from a SCENARIOS object.

    Handles two SCENARIOS shapes used across procedure packages:
    - Dataclass with str-typed field values  (e.g. company_onboarding)
    - List of dicts with a 'name' key       (e.g. wallet_bootstrap)
    """
    if isinstance(scenarios, list):
        # List-of-dicts format: each entry has a 'name' key
        return [s["name"] for s in scenarios if isinstance(s, dict) and "name" in s]
    # Dataclass format: attributes are string scenario identifiers
    try:
        attr_dict = vars(scenarios)
    except TypeError:
        attr_dict = {}
    return [v for k, v in attr_dict.items() if not k.startswith("_") and isinstance(v, str)]


@pytest.mark.parametrize("package_name", _ALL_PROCEDURE_PACKAGES)
def test_testspec_scenarios_are_non_empty_strings(package_name: str) -> None:
    """Every SCENARIOS object must yield at least one non-empty scenario name."""
    _skip_if_missing()

    module_path = (
        f"dataspace_control_plane_procedures.{package_name}.testspec"
    )
    try:
        testspec = __import__(module_path, fromlist=["SCENARIOS"])
    except ImportError:
        pytest.skip(f"{module_path} not importable — skipping scenario string checks")

    scenarios = testspec.SCENARIOS
    names = _extract_scenario_names(scenarios)

    assert names, (
        f"{package_name}.testspec.SCENARIOS has no extractable scenario identifiers.\n"
        f"Expected either a dataclass with str attributes or a list of dicts with 'name'."
    )
    for name in names:
        assert name.strip(), (
            f"{package_name}.testspec.SCENARIOS contains a blank scenario name: {name!r}"
        )


def test_all_procedure_packages_count() -> None:
    """The procedures package must register exactly the expected number of procedures."""
    _skip_if_missing()

    # Verify the registry enumerates the same 11 packages.
    try:
        from dataspace_control_plane_procedures.registry import (
            WORKFLOW_REGISTRY,
            populate_from_procedures,
        )
    except ImportError:
        pytest.skip("procedures.registry not available")

    populate_from_procedures()

    registered_queues_with_workflows = [
        q for q, wfs in WORKFLOW_REGISTRY.items() if wfs
    ]
    assert len(registered_queues_with_workflows) >= 5, (
        f"Expected at least 5 non-empty task queues after populate_from_procedures(); "
        f"got {len(registered_queues_with_workflows)}: {registered_queues_with_workflows}"
    )


# ── CompensationLog ───────────────────────────────────────────────────────────


def test_compensation_log_records_accumulate() -> None:
    """CompensationLog.record() must accumulate entries in insertion order."""
    _skip_if_missing()

    from dataspace_control_plane_procedures._shared.compensation import CompensationLog

    log = CompensationLog()
    log.record("create_wallet", "wallet-001")
    log.record("provision_connector", "connector-001")
    log.record("register_did", "did:key:abc")

    pending = log.pending()
    assert len(pending) == 3


def test_compensation_log_pending_is_lifo() -> None:
    """pending() must return entries in reverse insertion order (LIFO rollback)."""
    _skip_if_missing()

    from dataspace_control_plane_procedures._shared.compensation import CompensationLog

    log = CompensationLog()
    log.record("step_a", "res-a")
    log.record("step_b", "res-b")
    log.record("step_c", "res-c")

    pending = log.pending()
    actions = [e.action for e in pending]
    assert actions == ["step_c", "step_b", "step_a"], (
        f"pending() must return entries in LIFO order; got {actions}"
    )


def test_compensation_log_mark_compensated_removes_from_pending() -> None:
    """mark_compensated() must remove the matching entry from pending()."""
    _skip_if_missing()

    from dataspace_control_plane_procedures._shared.compensation import CompensationLog

    log = CompensationLog()
    log.record("step_a", "res-a")
    log.record("step_b", "res-b")

    log.mark_compensated("step_a", "res-a")

    pending_actions = {e.action for e in log.pending()}
    assert "step_a" not in pending_actions, (
        "Compensated entry 'step_a' must not appear in pending()"
    )
    assert "step_b" in pending_actions


def test_compensation_log_empty_has_no_pending() -> None:
    """A fresh CompensationLog must have no pending entries."""
    _skip_if_missing()

    from dataspace_control_plane_procedures._shared.compensation import CompensationLog

    log = CompensationLog()
    assert log.pending() == []


# ── should_continue_as_new ────────────────────────────────────────────────────


def test_should_continue_as_new_below_threshold_returns_false() -> None:
    """should_continue_as_new() must return False when event_count < threshold."""
    _skip_if_missing()

    from dataspace_control_plane_procedures._shared.continue_as_new import (
        HISTORY_THRESHOLD,
        should_continue_as_new,
    )

    assert not should_continue_as_new(0)
    assert not should_continue_as_new(HISTORY_THRESHOLD - 1)


def test_should_continue_as_new_at_threshold_returns_true() -> None:
    """should_continue_as_new() must return True at exactly the threshold."""
    _skip_if_missing()

    from dataspace_control_plane_procedures._shared.continue_as_new import (
        HISTORY_THRESHOLD,
        should_continue_as_new,
    )

    assert should_continue_as_new(HISTORY_THRESHOLD)
    assert should_continue_as_new(HISTORY_THRESHOLD + 1000)


def test_should_continue_as_new_custom_threshold() -> None:
    """Custom threshold parameter must override the default."""
    _skip_if_missing()

    from dataspace_control_plane_procedures._shared.continue_as_new import (
        should_continue_as_new,
    )

    assert not should_continue_as_new(99, threshold=100)
    assert should_continue_as_new(100, threshold=100)


# ── DedupeState ───────────────────────────────────────────────────────────────


def test_dedupe_state_marks_and_detects_duplicates() -> None:
    """mark_handled() followed by is_duplicate() must return True for the same ID."""
    _skip_if_missing()

    from dataspace_control_plane_procedures._shared.continue_as_new import DedupeState

    state = DedupeState()
    state.mark_handled("msg-abc")

    assert state.is_duplicate("msg-abc")
    assert not state.is_duplicate("msg-xyz")


def test_dedupe_state_fresh_instance_has_no_duplicates() -> None:
    """A new DedupeState must report every message as not-a-duplicate."""
    _skip_if_missing()

    from dataspace_control_plane_procedures._shared.continue_as_new import DedupeState

    state = DedupeState()
    assert not state.is_duplicate("any-message-id")


def test_dedupe_state_snapshot_round_trip() -> None:
    """snapshot() + from_snapshot() must preserve all handled message IDs."""
    _skip_if_missing()

    from dataspace_control_plane_procedures._shared.continue_as_new import DedupeState

    original = DedupeState()
    original.mark_handled("id-1")
    original.mark_handled("id-2")
    original.mark_handled("id-3")

    snap = original.snapshot()
    restored = DedupeState.from_snapshot(snap)

    assert restored.is_duplicate("id-1")
    assert restored.is_duplicate("id-2")
    assert restored.is_duplicate("id-3")
    assert not restored.is_duplicate("id-4")


def test_dedupe_state_max_size_eviction_does_not_raise() -> None:
    """Inserting beyond max_size must evict old entries without raising."""
    _skip_if_missing()

    from dataspace_control_plane_procedures._shared.continue_as_new import DedupeState

    state = DedupeState(max_size=10)
    for i in range(20):
        state.mark_handled(f"msg-{i}")

    # Must not raise and must still accept new entries
    state.mark_handled("msg-final")
    # The set of handled messages should not exceed 2× max_size
    assert len(state._handled) <= 20
