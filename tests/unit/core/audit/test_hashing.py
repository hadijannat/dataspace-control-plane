"""
tests/unit/core/audit/test_hashing.py
Unit tests for audit/hashing.py — HashDigest and digest_bytes().

Tests:
  1. digest_bytes() with SHA-256 produces the correct deterministic hex digest
  2. digest_bytes() with SHA-512 produces the correct deterministic hex digest
  3. digest_bytes() default algorithm is sha256
  4. digest_bytes() on empty bytes still returns a valid digest
  5. HashDigest is a frozen dataclass — mutation raises FrozenInstanceError
  6. Two calls to digest_bytes() on the same payload return equal HashDigest values
  7. digest_bytes() on different payloads returns distinct digests

All tests are pure logic — no network, no containers, no wall-clock side-effects.
Marker: unit
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_CORE_SRC = Path(__file__).resolve().parent.parent.parent.parent.parent / "core" / "src"
if _CORE_SRC.exists() and str(_CORE_SRC) not in sys.path:
    # Append rather than insert so that PYTHONPATH-provided paths take precedence.
    # This allows tests to run against the PR branch core when invoked via PYTHONPATH.
    sys.path.append(str(_CORE_SRC))

try:
    from dataspace_control_plane_core.audit.hashing import HashDigest, digest_bytes
    _AVAILABLE = True
except ImportError as _e:
    _AVAILABLE = False
    _IMPORT_ERROR = str(_e)


def _skip_if_missing() -> None:
    if not _AVAILABLE:
        pytest.skip(f"audit.hashing not available: {_IMPORT_ERROR}")


# ---------------------------------------------------------------------------
# HashDigest construction
# ---------------------------------------------------------------------------


def test_hash_digest_stores_algorithm_and_hex_value() -> None:
    """HashDigest must hold the algorithm and hex_value as given."""
    _skip_if_missing()
    d = HashDigest(algorithm="sha256", hex_value="deadbeef")
    assert d.algorithm == "sha256"
    assert d.hex_value == "deadbeef"


def test_hash_digest_is_frozen() -> None:
    """HashDigest is a frozen dataclass — assignment must raise."""
    _skip_if_missing()
    d = HashDigest(algorithm="sha256", hex_value="deadbeef")
    with pytest.raises((AttributeError, TypeError)):
        d.algorithm = "sha512"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# digest_bytes() correctness
# ---------------------------------------------------------------------------


def test_digest_bytes_sha256_matches_stdlib() -> None:
    """digest_bytes() with sha256 must produce the same digest as hashlib."""
    _skip_if_missing()
    payload = b"hello dataspace"
    expected = hashlib.sha256(payload).hexdigest()
    result = digest_bytes(payload, algorithm="sha256")
    assert result.algorithm == "sha256"
    assert result.hex_value == expected


def test_digest_bytes_sha512_matches_stdlib() -> None:
    """digest_bytes() with sha512 must produce the same digest as hashlib."""
    _skip_if_missing()
    payload = b"audit evidence"
    expected = hashlib.sha512(payload).hexdigest()
    result = digest_bytes(payload, algorithm="sha512")
    assert result.algorithm == "sha512"
    assert result.hex_value == expected


def test_digest_bytes_default_algorithm_is_sha256() -> None:
    """digest_bytes() without explicit algorithm must default to sha256."""
    _skip_if_missing()
    payload = b"default algorithm test"
    result = digest_bytes(payload)
    expected = hashlib.sha256(payload).hexdigest()
    assert result.algorithm == "sha256"
    assert result.hex_value == expected


def test_digest_bytes_empty_payload_produces_valid_digest() -> None:
    """digest_bytes() on empty bytes must still return a valid, deterministic digest."""
    _skip_if_missing()
    result = digest_bytes(b"")
    expected = hashlib.sha256(b"").hexdigest()
    assert result.hex_value == expected
    assert len(result.hex_value) == 64  # SHA-256 hex is 64 chars


def test_digest_bytes_same_input_produces_equal_results() -> None:
    """digest_bytes() called twice on identical input must return equal HashDigest instances."""
    _skip_if_missing()
    payload = b"deterministic fixture"
    r1 = digest_bytes(payload, algorithm="sha256")
    r2 = digest_bytes(payload, algorithm="sha256")
    assert r1 == r2


def test_digest_bytes_different_inputs_produce_distinct_digests() -> None:
    """digest_bytes() on different payloads must produce distinct digests."""
    _skip_if_missing()
    r1 = digest_bytes(b"payload-alpha", algorithm="sha256")
    r2 = digest_bytes(b"payload-beta", algorithm="sha256")
    assert r1 != r2
    assert r1.hex_value != r2.hex_value
