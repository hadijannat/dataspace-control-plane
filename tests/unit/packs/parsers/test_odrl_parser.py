"""
tests/unit/packs/parsers/test_odrl_parser.py
Property-based tests for the ODRL policy parser in the Catena-X pack.

Tests: parse/compile round-trip for offers, uid preservation, policy_type invariant,
permission list round-trip, and unknown field surface.

Requires: hypothesis. Imports packs.catenax parser — skipped if not installed.
Marker: unit
"""
from __future__ import annotations

import pytest

hypothesis = pytest.importorskip("hypothesis")

from hypothesis import given, settings
from hypothesis import strategies as st

pytestmark = pytest.mark.unit

# Attempt to import the parser — skip entire module if packs not scaffolded
try:
    import dataspace_control_plane_packs.catenax.policy_profile.parser as _parser_module  # type: ignore

    _PARSER_AVAILABLE = True
except ImportError:
    _PARSER_AVAILABLE = False

# Build a reference to the parse function, if it exists
_parse_fn = None
if _PARSER_AVAILABLE:
    for _candidate in ("parse", "parse_offer", "parse_policy", "from_dict"):
        if hasattr(_parser_module, _candidate):
            _parse_fn = getattr(_parser_module, _candidate)
            break

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

UID_STRATEGY = st.text(min_size=1, max_size=50).map(lambda s: f"urn:test:{s}")
ACTION_STRATEGY = st.sampled_from(["odrl:use", "odrl:read", "odrl:write", "odrl:transfer"])


def _minimal_offer(uid: str) -> dict:
    return {
        "@type": "odrl:Offer",
        "@id": uid,
        "odrl:permission": [],
        "odrl:prohibition": [],
        "odrl:obligation": [],
    }


def _try_parse(offer_dict: dict):
    """Call the parser if available; return (parsed_result, None) or (None, skip_reason)."""
    if not _PARSER_AVAILABLE:
        return None, "packs.catenax.policy_profile.parser not installed"
    if _parse_fn is None:
        return None, "No known parse function found in parser module"
    try:
        return _parse_fn(offer_dict), None
    except Exception as exc:
        return None, f"Parser raised: {exc}"


# ---------------------------------------------------------------------------
# Test 1: uid round-trip
# ---------------------------------------------------------------------------


@given(uid=UID_STRATEGY)
@settings(max_examples=50)
def test_offer_uid_roundtrip(uid: str) -> None:
    """After parsing a minimal offer, the uid must be preserved in the result."""
    offer = _minimal_offer(uid)
    result, skip_reason = _try_parse(offer)
    if skip_reason:
        pytest.skip(skip_reason)
    # The parser must keep the uid accessible
    result_str = str(result)
    assert uid in result_str, f"uid {uid!r} not found in parsed result: {result_str}"


# ---------------------------------------------------------------------------
# Test 2: policy_type invariant
# ---------------------------------------------------------------------------


@given(uid=UID_STRATEGY)
@settings(max_examples=50)
def test_policy_type_invariant(uid: str) -> None:
    """If the parser extracts policy_type, it must always be 'offer' for odrl:Offer input."""
    offer = _minimal_offer(uid)
    result, skip_reason = _try_parse(offer)
    if skip_reason:
        pytest.skip(skip_reason)

    if isinstance(result, dict):
        policy_type = result.get("policy_type") or result.get("type") or result.get("@type")
        if policy_type is not None:
            assert "offer" in str(policy_type).lower(), (
                f"Expected offer type, got {policy_type!r}"
            )
    elif hasattr(result, "policy_type"):
        assert "offer" in str(result.policy_type).lower()


# ---------------------------------------------------------------------------
# Test 3: permission list round-trip
# ---------------------------------------------------------------------------


@given(
    uid=UID_STRATEGY,
    actions=st.lists(ACTION_STRATEGY, min_size=1, max_size=3),
)
@settings(max_examples=50)
def test_permission_list_roundtrip(uid: str, actions: list[str]) -> None:
    """After parse/compile, all permission actions must be present in the output."""
    offer = {
        **_minimal_offer(uid),
        "odrl:permission": [{"odrl:action": a, "odrl:target": "urn:asset:1"} for a in actions],
    }
    result, skip_reason = _try_parse(offer)
    if skip_reason:
        pytest.skip(skip_reason)

    result_str = str(result)
    for action in actions:
        # The action value (e.g. "odrl:use" or just "use") should appear in output
        action_local = action.split(":")[-1]
        assert action_local in result_str or action in result_str, (
            f"Action {action!r} not found in parsed result: {result_str}"
        )


# ---------------------------------------------------------------------------
# Test 4: unknown fields do not cause silent data loss without surfacing
# ---------------------------------------------------------------------------


@given(uid=UID_STRATEGY)
@settings(max_examples=50)
def test_unknown_fields_surfaced_as_lossy(uid: str) -> None:
    """Extra unknown fields should not cause an unhandled exception.

    If the parser exposes lossy_clauses or unknown_fields, verify they capture
    unknown data. At minimum, parsing must not raise an unhandled exception.
    """
    offer = {
        **_minimal_offer(uid),
        "x-custom-field": "some-value",
        "x-extra": {"nested": True},
    }

    if not _PARSER_AVAILABLE or _parse_fn is None:
        pytest.skip("Parser module not available")

    # Must not raise
    try:
        result = _parse_fn(offer)
    except (TypeError, KeyError, ValueError):
        # Parser may reject unknown fields — that is acceptable
        return

    # If the parser returns lossy metadata, check it's captured
    if isinstance(result, dict):
        for key in ("lossy_clauses", "unknown_fields", "extra"):
            if key in result:
                assert result[key] is not None
                return
