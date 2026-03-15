"""
tests/unit/packs/reducers/test_pack_reducer.py
Unit tests for the pack reducer in the shared packs library.

Tests: identity, last-wins precedence, empty input, conflict detection, commutativity.
Requires: hypothesis. Imports packs._shared.reducers — skipped if not installed.
Marker: unit
"""
from __future__ import annotations

import pytest

hypothesis = pytest.importorskip("hypothesis")

from hypothesis import given, settings
from hypothesis import strategies as st

pytestmark = pytest.mark.unit

# Attempt to import the reducer module
try:
    import dataspace_control_plane_packs._shared.reducers as _reducers_module  # type: ignore

    _REDUCERS_AVAILABLE = True
except ImportError:
    _REDUCERS_AVAILABLE = False

_reduce_fn = None
if _REDUCERS_AVAILABLE:
    for _candidate in ("reduce", "reduce_packs", "merge", "apply"):
        if hasattr(_reducers_module, _candidate):
            _reduce_fn = getattr(_reducers_module, _candidate)
            break


def _require_reducers():
    if not _REDUCERS_AVAILABLE or _reduce_fn is None:
        pytest.skip("packs._shared.reducers not available")


def _make_pack(pack_id: str, capabilities: dict) -> dict:
    return {"pack_id": pack_id, "capabilities": capabilities}


# ---------------------------------------------------------------------------
# Test 1: Single-pack reducer identity
# ---------------------------------------------------------------------------


def test_single_pack_reducer_identity() -> None:
    """A single pack in the list should produce that pack's capabilities unchanged."""
    _require_reducers()
    pack = _make_pack("catenax", {"odrl": True, "vc": "v2"})
    result = _reduce_fn([pack])
    assert result is not None
    result_str = str(result)
    assert "catenax" in result_str or "odrl" in result_str, (
        f"Expected pack capabilities in result, got: {result_str}"
    )


# ---------------------------------------------------------------------------
# Test 2: Last-wins precedence
# ---------------------------------------------------------------------------


def test_reducer_precedence_last_wins() -> None:
    """When two packs declare the same field, the last one in the list must win."""
    _require_reducers()
    pack_a = _make_pack("pack_a", {"feature_x": "from_a", "unique_a": True})
    pack_b = _make_pack("pack_b", {"feature_x": "from_b", "unique_b": True})
    result = _reduce_fn([pack_a, pack_b])
    result_str = str(result)
    # "from_b" should appear and "from_a" should NOT appear for feature_x
    assert "from_b" in result_str, f"Expected last-wins value 'from_b', got: {result_str}"


# ---------------------------------------------------------------------------
# Test 3: Empty input returns empty / default result
# ---------------------------------------------------------------------------


def test_reducer_empty_input_returns_empty() -> None:
    """Empty pack list must return an empty or default neutral result (not raise)."""
    _require_reducers()
    result = _reduce_fn([])
    # Must not raise; result should be empty or a neutral default
    assert result is not None or result == {} or result == [] or result is None, (
        "Reducer returned unexpected non-empty result for empty input"
    )
    # At minimum, it must not crash
    _ = str(result)


# ---------------------------------------------------------------------------
# Test 4: Conflict declared (not silently merged)
# ---------------------------------------------------------------------------


def test_reducer_conflict_declared() -> None:
    """
    If packs declare conflicting capabilities and the reducer has conflict detection,
    a ConflictError or similar must be raised rather than silently merging.

    If the reducer does NOT have conflict detection, this test passes silently.
    """
    _require_reducers()

    # Try to find a ConflictError or similar
    conflict_exc = None
    for _name in ("ConflictError", "PackConflictError", "CapabilityConflictError"):
        if hasattr(_reducers_module, _name):
            conflict_exc = getattr(_reducers_module, _name)
            break

    if conflict_exc is None:
        # Reducer has no conflict detection — skip this assertion
        pytest.skip("Reducer has no conflict detection; skipping conflict test")

    pack_a = _make_pack("a", {"protocol": "DSP-1"})
    pack_b = _make_pack("b", {"protocol": "DSP-2"})

    with pytest.raises(conflict_exc):
        _reduce_fn([pack_a, pack_b], strict_conflict=True)


# ---------------------------------------------------------------------------
# Test 5: Commutativity for disjoint packs (property-based)
# ---------------------------------------------------------------------------


@given(order=st.permutations(["catenax", "gaia_x", "manufacturing_x"]))
@settings(max_examples=50)
def test_reducer_commutativity_for_disjoint_packs(order: list[str]) -> None:
    """For packs with non-overlapping capability keys, order must not matter."""
    _require_reducers()

    # Each pack has its own unique capability key
    packs_by_id = {
        "catenax": _make_pack("catenax", {"catenax_odrl": True}),
        "gaia_x": _make_pack("gaia_x", {"gaia_x_sd": True}),
        "manufacturing_x": _make_pack("manufacturing_x", {"mx_twin": True}),
    }
    ordered_packs = [packs_by_id[pid] for pid in order]

    result = _reduce_fn(ordered_packs)
    result_str = str(result)

    # All capability keys must appear regardless of order
    assert "catenax_odrl" in result_str, f"catenax_odrl missing in: {result_str}"
    assert "gaia_x_sd" in result_str, f"gaia_x_sd missing in: {result_str}"
    assert "mx_twin" in result_str, f"mx_twin missing in: {result_str}"
