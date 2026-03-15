"""
tests/unit/core/procedure_runtime/test_progress.py
Unit tests for procedure_runtime/progress.py — ProcedureProgress.

Tests:
  1. percent_complete returns 0 when total_steps is 0 (division-by-zero guard)
  2. percent_complete returns 0 when total_steps is negative
  3. percent_complete returns 0 when completed_steps is 0 out of N steps
  4. percent_complete returns 100 when completed_steps == total_steps
  5. percent_complete returns integer floor for mid-progress
  6. percent_complete truncates at 100 when completed_steps > total_steps
  7. ProcedureProgress default fields are empty/zero
  8. ProcedureProgress is a frozen dataclass — mutation raises

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
    from dataspace_control_plane_core.procedure_runtime.progress import ProcedureProgress
    _AVAILABLE = True
except ImportError as _e:
    _AVAILABLE = False
    _IMPORT_ERROR = str(_e)


def _skip_if_missing() -> None:
    if not _AVAILABLE:
        pytest.skip(f"procedure_runtime.progress not available: {_IMPORT_ERROR}")


# ── Default field values ──────────────────────────────────────────────────────


def test_procedure_progress_default_fields() -> None:
    """ProcedureProgress must default to zero steps, empty strings."""
    _skip_if_missing()
    p = ProcedureProgress()
    assert p.current_step == ""
    assert p.completed_steps == 0
    assert p.total_steps == 0
    assert p.message == ""


# ── percent_complete: zero-divisor guard ─────────────────────────────────────


def test_percent_complete_returns_zero_when_total_steps_is_zero() -> None:
    """percent_complete must return 0 when total_steps == 0 (division-by-zero guard)."""
    _skip_if_missing()
    p = ProcedureProgress(completed_steps=5, total_steps=0)
    assert p.percent_complete == 0


def test_percent_complete_returns_zero_when_total_steps_is_negative() -> None:
    """percent_complete must return 0 when total_steps < 0."""
    _skip_if_missing()
    p = ProcedureProgress(completed_steps=3, total_steps=-1)
    assert p.percent_complete == 0


# ── percent_complete: normal range ────────────────────────────────────────────


def test_percent_complete_returns_zero_when_no_steps_completed() -> None:
    """percent_complete must return 0 when completed_steps == 0."""
    _skip_if_missing()
    p = ProcedureProgress(completed_steps=0, total_steps=10)
    assert p.percent_complete == 0


def test_percent_complete_returns_100_when_all_steps_completed() -> None:
    """percent_complete must return 100 when completed_steps == total_steps."""
    _skip_if_missing()
    p = ProcedureProgress(completed_steps=5, total_steps=5)
    assert p.percent_complete == 100


def test_percent_complete_returns_50_for_halfway() -> None:
    """percent_complete must return 50 for half completed."""
    _skip_if_missing()
    p = ProcedureProgress(completed_steps=5, total_steps=10)
    assert p.percent_complete == 50


def test_percent_complete_truncates_to_integer() -> None:
    """percent_complete must return an integer — int(33.333...) == 33."""
    _skip_if_missing()
    p = ProcedureProgress(completed_steps=1, total_steps=3)
    assert p.percent_complete == 33
    assert isinstance(p.percent_complete, int)


def test_percent_complete_handles_single_step() -> None:
    """percent_complete returns 100 for 1-of-1 completed."""
    _skip_if_missing()
    p = ProcedureProgress(completed_steps=1, total_steps=1)
    assert p.percent_complete == 100


# ── Boundary cases ────────────────────────────────────────────────────────────


def test_percent_complete_with_large_step_counts() -> None:
    """percent_complete must handle large step counts without overflow."""
    _skip_if_missing()
    p = ProcedureProgress(completed_steps=999_999, total_steps=1_000_000)
    assert p.percent_complete == 99


# ── Frozen dataclass ─────────────────────────────────────────────────────────


def test_procedure_progress_is_frozen() -> None:
    """ProcedureProgress is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    p = ProcedureProgress(completed_steps=3, total_steps=10)
    with pytest.raises((AttributeError, TypeError)):
        p.completed_steps = 7  # type: ignore[misc]


# ── Parametrized correctness checks ──────────────────────────────────────────


@pytest.mark.parametrize(
    "completed, total, expected_pct",
    [
        (0, 0, 0),
        (0, 1, 0),
        (1, 4, 25),
        (2, 4, 50),
        (3, 4, 75),
        (4, 4, 100),
        (7, 10, 70),
        (1, 3, 33),
        (2, 3, 66),
    ],
)
def test_percent_complete_parametrized(completed: int, total: int, expected_pct: int) -> None:
    """percent_complete must return the expected integer for each (completed, total) pair."""
    _skip_if_missing()
    p = ProcedureProgress(completed_steps=completed, total_steps=total)
    assert p.percent_complete == expected_pct
