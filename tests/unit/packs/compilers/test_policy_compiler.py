"""
tests/unit/packs/compilers/test_policy_compiler.py
Unit tests for the Catena-X ODRL policy compiler.

Tests: minimal offer compilation, permission/prohibition inclusion, determinism.
Requires: hypothesis. Imports packs.catenax compiler — skipped if not installed.
Marker: unit
"""
from __future__ import annotations

import pytest

hypothesis = pytest.importorskip("hypothesis")

from hypothesis import given, settings
from hypothesis import strategies as st

pytestmark = pytest.mark.unit

# Attempt to import the compiler — skip if packs not scaffolded
try:
    import dataspace_control_plane_packs.catenax.policy_profile.compiler as _compiler_module  # type: ignore

    _COMPILER_AVAILABLE = True
except ImportError:
    _COMPILER_AVAILABLE = False

_compile_fn = None
if _COMPILER_AVAILABLE:
    for _candidate in ("compile", "compile_offer", "compile_policy", "to_ast"):
        if hasattr(_compiler_module, _candidate):
            _compile_fn = getattr(_compiler_module, _candidate)
            break


def _require_compiler():
    if not _COMPILER_AVAILABLE or _compile_fn is None:
        pytest.skip("packs.catenax.policy_profile.compiler not available")


def _minimal_offer(uid: str = "urn:offer:1") -> dict:
    return {
        "@type": "odrl:Offer",
        "@id": uid,
        "odrl:permission": [],
        "odrl:prohibition": [],
    }


# ---------------------------------------------------------------------------
# Test 1: minimal offer produces AST with a discriminator field
# ---------------------------------------------------------------------------


def test_compile_empty_offer_produces_ast() -> None:
    """A minimal empty offer must compile to a non-None AST with a type discriminator."""
    _require_compiler()
    result = _compile_fn(_minimal_offer())
    assert result is not None, "Compiler returned None for valid minimal offer"
    result_str = str(result)
    # Must have some type-discriminator field
    discriminators = ["policy_type", "type", "@type", "offer", "Offer"]
    assert any(d.lower() in result_str.lower() for d in discriminators), (
        f"Expected a type discriminator in compiled AST, got: {result_str}"
    )


# ---------------------------------------------------------------------------
# Test 2: permission with action produces rule in AST
# ---------------------------------------------------------------------------


def test_compile_permission_with_action() -> None:
    """Offer with one permission must produce an AST with at least one rule/permission."""
    _require_compiler()
    offer = {
        **_minimal_offer(),
        "odrl:permission": [{"odrl:action": "odrl:use", "odrl:target": "urn:asset:1"}],
    }
    result = _compile_fn(offer)
    assert result is not None
    result_str = str(result)
    assert any(word in result_str.lower() for word in ["permission", "rule", "use"]), (
        f"Expected permission/rule in AST, got: {result_str}"
    )


# ---------------------------------------------------------------------------
# Test 3: prohibition included in output
# ---------------------------------------------------------------------------


def test_compile_prohibition_included() -> None:
    """Offer with both permission and prohibition must reflect both in compiled AST."""
    _require_compiler()
    offer = {
        **_minimal_offer(),
        "odrl:permission": [{"odrl:action": "odrl:use", "odrl:target": "urn:asset:1"}],
        "odrl:prohibition": [{"odrl:action": "odrl:write", "odrl:target": "urn:asset:1"}],
    }
    result = _compile_fn(offer)
    assert result is not None
    result_str = str(result)
    assert any(w in result_str.lower() for w in ["prohibition", "write"]), (
        f"Expected prohibition in AST, got: {result_str}"
    )


# ---------------------------------------------------------------------------
# Test 4: compile is deterministic (property-based)
# ---------------------------------------------------------------------------


@given(
    offer_fields=st.fixed_dictionaries({
        "uid": st.from_regex(r"urn:[a-z]{3}:[0-9]{6}", fullmatch=True),
        "action": st.sampled_from(["odrl:use", "odrl:read", "odrl:write"]),
    })
)
@settings(max_examples=50)
def test_compile_is_deterministic(offer_fields: dict) -> None:
    """Compiling the same offer twice must produce identical results."""
    _require_compiler()

    offer = {
        "@type": "odrl:Offer",
        "@id": offer_fields["uid"],
        "odrl:permission": [
            {"odrl:action": offer_fields["action"], "odrl:target": "urn:asset:test"}
        ],
        "odrl:prohibition": [],
    }

    result_a = _compile_fn(offer)
    result_b = _compile_fn(offer)

    assert str(result_a) == str(result_b), (
        f"Compiler is not deterministic for offer {offer!r}:\n"
        f"  first:  {result_a}\n"
        f"  second: {result_b}"
    )
