"""
tests/unit/core/procedure_runtime/test_retry_policy.py
Unit tests for procedure_runtime/retry_policy.py — RetryPolicy.

Tests:
  1. RetryPolicy stores max_attempts, intervals, backoff_coefficient correctly
  2. RetryPolicy defaults match documented safe defaults
  3. RetryPolicy with non-retryable_error_codes tuple
  4. RetryPolicy is a frozen dataclass — mutation raises
  5. Two RetryPolicy instances with identical fields are equal

All tests are pure logic — no network, no containers.
Marker: unit
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_CORE_SRC = Path(__file__).resolve().parent.parent.parent.parent.parent / "core" / "src"
if _CORE_SRC.exists() and str(_CORE_SRC) not in sys.path:
    # Append rather than insert so that PYTHONPATH-provided paths take precedence.
    sys.path.append(str(_CORE_SRC))

try:
    from dataspace_control_plane_core.procedure_runtime.retry_policy import RetryPolicy
    _AVAILABLE = True
except ImportError as _e:
    _AVAILABLE = False
    _IMPORT_ERROR = str(_e)


def _skip_if_missing() -> None:
    if not _AVAILABLE:
        pytest.skip(f"procedure_runtime.retry_policy not available: {_IMPORT_ERROR}")


def test_retry_policy_default_values() -> None:
    """RetryPolicy must have documented default values for all fields."""
    _skip_if_missing()
    rp = RetryPolicy()
    assert rp.max_attempts == 3
    assert rp.initial_interval_seconds == 5
    assert rp.backoff_coefficient == 2.0
    assert rp.max_interval_seconds == 60
    assert rp.non_retryable_error_codes == ()


def test_retry_policy_stores_explicit_values() -> None:
    """RetryPolicy must store explicitly supplied values."""
    _skip_if_missing()
    rp = RetryPolicy(
        max_attempts=10,
        initial_interval_seconds=1,
        backoff_coefficient=1.5,
        max_interval_seconds=300,
    )
    assert rp.max_attempts == 10
    assert rp.initial_interval_seconds == 1
    assert rp.backoff_coefficient == 1.5
    assert rp.max_interval_seconds == 300


def test_retry_policy_with_non_retryable_error_codes() -> None:
    """RetryPolicy must store a non-empty non_retryable_error_codes tuple."""
    _skip_if_missing()
    rp = RetryPolicy(non_retryable_error_codes=("VALIDATION_ERROR", "PERMISSION_DENIED"))
    assert "VALIDATION_ERROR" in rp.non_retryable_error_codes
    assert "PERMISSION_DENIED" in rp.non_retryable_error_codes
    assert len(rp.non_retryable_error_codes) == 2


def test_retry_policy_is_frozen() -> None:
    """RetryPolicy is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    rp = RetryPolicy()
    with pytest.raises((AttributeError, TypeError)):
        rp.max_attempts = 99  # type: ignore[misc]


def test_retry_policy_equality() -> None:
    """Two RetryPolicy instances with identical fields must be equal."""
    _skip_if_missing()
    rp1 = RetryPolicy(max_attempts=5, initial_interval_seconds=2)
    rp2 = RetryPolicy(max_attempts=5, initial_interval_seconds=2)
    assert rp1 == rp2


def test_retry_policy_inequality() -> None:
    """Two RetryPolicy instances with different max_attempts must not be equal."""
    _skip_if_missing()
    rp1 = RetryPolicy(max_attempts=3)
    rp2 = RetryPolicy(max_attempts=5)
    assert rp1 != rp2
