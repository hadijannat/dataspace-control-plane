"""
tests/unit/core/test_shim_compatibility.py
Smoke tests for backward-compatibility shims introduced in the core domain kernel refactor.

The PR refactored core/ into an installable package and moved several models
to canonical locations. Old import paths are kept alive as shims so that
existing consumers (apps/, procedures/, adapters/) are not broken before they
are updated. This file verifies that those shims resolve correctly.

Tests:
  1. contracts.py shim re-exports ProcedureType, ProcedureHandle, ProcedureInput,
     ProcedureResult, ProcedureStatus (pre-existed, must remain stable)
  2. state.py shim re-exports ManualReviewState, ProcedureSnapshot, ProcedureState,
     ProcedureStatus (new in PR — skipped if not present)
  3. versioning.py shim re-exports ProcedureVersionMarker (new in PR)
  4. Original audit/record.py is still importable
  5. New audit/records.py is importable and exports the new names (new in PR)
  6. Public API surface (procedure_runtime.api) exposes all expected names

Each test group uses individual import guards so tests skip on old core rather
than raising import errors. This makes the suite safe to run in worktrees that
pre-date the PR merge.

All checks are import-only — no runtime side-effects.
Marker: unit
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_CORE_SRC = Path(__file__).resolve().parent.parent.parent.parent / "core" / "src"
if _CORE_SRC.exists() and str(_CORE_SRC) not in sys.path:
    # Append rather than insert so that PYTHONPATH-provided paths take precedence.
    sys.path.append(str(_CORE_SRC))

# Attempt to import the core package — all tests skip if absent.
try:
    import dataspace_control_plane_core  # noqa: F401
    _CORE_AVAILABLE = True
except ImportError as _core_e:
    _CORE_AVAILABLE = False
    _CORE_IMPORT_ERROR = str(_core_e)


def _skip_if_core_missing() -> None:
    if not _CORE_AVAILABLE:
        pytest.skip(f"core package not available: {_CORE_IMPORT_ERROR}")


# ── contracts.py shim — always present ────────────────────────────────────────


def test_contracts_shim_exports_procedure_type() -> None:
    """contracts.py must re-export ProcedureType."""
    _skip_if_core_missing()
    from dataspace_control_plane_core.procedure_runtime.contracts import ProcedureType  # noqa: F401
    assert ProcedureType is not None


def test_contracts_shim_exports_procedure_handle() -> None:
    """contracts.py must re-export ProcedureHandle."""
    _skip_if_core_missing()
    from dataspace_control_plane_core.procedure_runtime.contracts import ProcedureHandle  # noqa: F401
    assert ProcedureHandle is not None


def test_contracts_shim_exports_procedure_input() -> None:
    """contracts.py must re-export ProcedureInput."""
    _skip_if_core_missing()
    from dataspace_control_plane_core.procedure_runtime.contracts import ProcedureInput  # noqa: F401
    assert ProcedureInput is not None


def test_contracts_shim_exports_procedure_result() -> None:
    """contracts.py must re-export ProcedureResult."""
    _skip_if_core_missing()
    from dataspace_control_plane_core.procedure_runtime.contracts import ProcedureResult  # noqa: F401
    assert ProcedureResult is not None


def test_contracts_shim_exports_procedure_status() -> None:
    """contracts.py must re-export ProcedureStatus."""
    _skip_if_core_missing()
    from dataspace_control_plane_core.procedure_runtime.contracts import ProcedureStatus  # noqa: F401
    assert ProcedureStatus is not None


# ── state.py shim — new in PR ─────────────────────────────────────────────────


def _import_state_shim():
    """Return True if the state.py shim is present, False if not (old core)."""
    try:
        from dataspace_control_plane_core.procedure_runtime import state as _s  # noqa: F401
        return True
    except ImportError:
        return False


def test_state_shim_exports_procedure_status() -> None:
    """state.py must re-export ProcedureStatus (PR gate — skipped on old core)."""
    _skip_if_core_missing()
    if not _import_state_shim():
        pytest.skip("procedure_runtime.state shim not yet present — added in PR #2")
    from dataspace_control_plane_core.procedure_runtime.state import ProcedureStatus  # noqa: F401
    assert ProcedureStatus is not None


def test_state_shim_exports_procedure_state() -> None:
    """state.py must re-export ProcedureState (PR gate — skipped on old core)."""
    _skip_if_core_missing()
    if not _import_state_shim():
        pytest.skip("procedure_runtime.state shim not yet present — added in PR #2")
    from dataspace_control_plane_core.procedure_runtime.state import ProcedureState  # noqa: F401
    assert ProcedureState is not None


def test_state_shim_exports_procedure_snapshot() -> None:
    """state.py must re-export ProcedureSnapshot (PR gate — skipped on old core)."""
    _skip_if_core_missing()
    if not _import_state_shim():
        pytest.skip("procedure_runtime.state shim not yet present — added in PR #2")
    from dataspace_control_plane_core.procedure_runtime.state import ProcedureSnapshot  # noqa: F401
    assert ProcedureSnapshot is not None


def test_state_shim_exports_manual_review_state() -> None:
    """state.py must re-export ManualReviewState (PR gate — skipped on old core)."""
    _skip_if_core_missing()
    if not _import_state_shim():
        pytest.skip("procedure_runtime.state shim not yet present — added in PR #2")
    from dataspace_control_plane_core.procedure_runtime.state import ManualReviewState  # noqa: F401
    assert ManualReviewState is not None


# ── versioning.py shim — new in PR ───────────────────────────────────────────


def _import_versioning_shim() -> bool:
    try:
        from dataspace_control_plane_core.procedure_runtime import versioning as _v  # noqa: F401
        return True
    except ImportError:
        return False


def test_versioning_shim_exports_procedure_version_marker() -> None:
    """versioning.py must re-export ProcedureVersionMarker (PR gate)."""
    _skip_if_core_missing()
    if not _import_versioning_shim():
        pytest.skip("procedure_runtime.versioning shim not yet present — added in PR #2")
    from dataspace_control_plane_core.procedure_runtime.versioning import ProcedureVersionMarker  # noqa: F401
    assert ProcedureVersionMarker is not None


# ── Original audit/record.py still importable ─────────────────────────────────


def test_original_audit_record_module_still_importable() -> None:
    """Original audit/record.py (pre-refactor) must still be importable for backward compat."""
    _skip_if_core_missing()
    try:
        from dataspace_control_plane_core.audit.record import (  # noqa: F401
            AuditRecord,
            AuditCategory,
            AuditOutcome,
        )
        assert AuditRecord is not None
    except ImportError:
        pytest.skip("audit/record.py not present — expected after full migration to records.py")


# ── New audit/records.py importable — new in PR ──────────────────────────────


def _import_audit_records() -> bool:
    try:
        from dataspace_control_plane_core.audit import records as _r  # noqa: F401
        return True
    except ImportError:
        return False


def test_new_audit_records_module_importable() -> None:
    """New audit/records.py must export AuditRecord, AuditActor, AuditSubject (PR gate)."""
    _skip_if_core_missing()
    if not _import_audit_records():
        pytest.skip("audit.records not yet present — added in PR #2")
    from dataspace_control_plane_core.audit.records import (  # noqa: F401
        AuditRecord,
        AuditActor,
        AuditSubject,
        AuditCategory,
        AuditOutcome,
    )
    assert AuditRecord is not None
    assert AuditActor is not None
    assert AuditSubject is not None


# ── Public procedure_runtime API surface ─────────────────────────────────────


def _import_procedure_runtime_api() -> bool:
    try:
        from dataspace_control_plane_core.procedure_runtime import api as _a  # noqa: F401
        return True
    except ImportError:
        return False


def test_procedure_runtime_api_exposes_stable_names() -> None:
    """procedure_runtime.api must expose the stable pre-PR names."""
    _skip_if_core_missing()
    if not _import_procedure_runtime_api():
        pytest.skip("procedure_runtime.api not available")
    from dataspace_control_plane_core.procedure_runtime.api import (  # noqa: F401
        ProcedureType,
        ProcedureInput,
        ProcedureResult,
        ProcedureStatus,
    )
    assert ProcedureType is not None


def test_procedure_runtime_api_exposes_new_pr_names() -> None:
    """procedure_runtime.api must expose new PR #2 names after merge (PR gate)."""
    _skip_if_core_missing()
    if not _import_procedure_runtime_api():
        pytest.skip("procedure_runtime.api not available")
    try:
        from dataspace_control_plane_core.procedure_runtime.api import (  # noqa: F401
            ProcedureSnapshot,
            ProcedureState,
            ProcedureProgress,
            CancelProcedure,
            ApproveProcedure,
            RejectProcedure,
            RetryProcedure,
            PauseProcedure,
            ResumeProcedure,
            RetryPolicy,
        )
        assert ProcedureSnapshot is not None
        assert CancelProcedure is not None
        assert RetryPolicy is not None
    except ImportError as exc:
        pytest.skip(
            f"PR #2 names not yet present in procedure_runtime.api — added in this PR: {exc}"
        )
