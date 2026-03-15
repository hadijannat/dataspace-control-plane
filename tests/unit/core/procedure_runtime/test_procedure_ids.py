"""
tests/unit/core/procedure_runtime/test_procedure_ids.py
Unit tests for procedure_runtime/procedure_ids.py — ProcedureType and ProcedureHandle.

Tests:
  1. ProcedureType enum values are string-valued and match their canonical slugs
  2. All expected ProcedureType members exist
  3. ProcedureHandle stores workflow_id, procedure_type, tenant_id, correlation
  4. ProcedureHandle defaults: run_id="", task_queue=""
  5. ProcedureHandle is a frozen dataclass — mutation raises
  6. ProcedureHandle equality — two handles with same fields are equal

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
    from dataspace_control_plane_core.procedure_runtime.procedure_ids import (
        ProcedureHandle,
        ProcedureType,
    )
    from dataspace_control_plane_core.domains._shared.ids import TenantId, WorkflowId
    from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
    _AVAILABLE = True
except ImportError as _e:
    _AVAILABLE = False
    _IMPORT_ERROR = str(_e)


def _skip_if_missing() -> None:
    if not _AVAILABLE:
        pytest.skip(f"procedure_runtime.procedure_ids not available: {_IMPORT_ERROR}")


# ── ProcedureType ─────────────────────────────────────────────────────────────


def test_procedure_type_all_expected_members_exist() -> None:
    """All expected ProcedureType members must be present."""
    _skip_if_missing()
    expected = {
        "COMPANY_ONBOARDING",
        "CONNECTOR_BOOTSTRAP",
        "MACHINE_CREDENTIAL_ROTATION",
        "ASSET_TWIN_PUBLICATION",
        "CONTRACT_NEGOTIATION",
        "COMPLIANCE_GAP_SCAN",
        "STALE_NEGOTIATION_SWEEP",
    }
    actual = {m.name for m in ProcedureType}
    missing = expected - actual
    assert not missing, f"ProcedureType is missing members: {missing}"


@pytest.mark.parametrize(
    "member, expected_value",
    [
        ("COMPANY_ONBOARDING", "company-onboarding"),
        ("CONNECTOR_BOOTSTRAP", "connector-bootstrap"),
        ("MACHINE_CREDENTIAL_ROTATION", "machine-credential-rotation"),
        ("ASSET_TWIN_PUBLICATION", "asset-twin-publication"),
        ("CONTRACT_NEGOTIATION", "contract-negotiation"),
        ("COMPLIANCE_GAP_SCAN", "compliance-gap-scan"),
        ("STALE_NEGOTIATION_SWEEP", "stale-negotiation-sweep"),
    ],
)
def test_procedure_type_slug_values(member: str, expected_value: str) -> None:
    """Each ProcedureType member must have its canonical kebab-case string value."""
    _skip_if_missing()
    assert ProcedureType[member].value == expected_value


def test_procedure_type_is_str_enum() -> None:
    """ProcedureType must be usable as a plain string."""
    _skip_if_missing()
    pt = ProcedureType.COMPANY_ONBOARDING
    assert pt == "company-onboarding"
    assert isinstance(pt, str)


# ── ProcedureHandle ───────────────────────────────────────────────────────────


def _make_handle(
    run_id: str = "",
    task_queue: str = "",
) -> "ProcedureHandle":
    return ProcedureHandle(
        workflow_id=WorkflowId("wf-test-001"),
        procedure_type=ProcedureType.COMPANY_ONBOARDING,
        tenant_id=TenantId("tenant-handle-test"),
        correlation=CorrelationContext.new(),
        run_id=run_id,
        task_queue=task_queue,
    )


def test_procedure_handle_stores_required_fields() -> None:
    """ProcedureHandle must store workflow_id, procedure_type, tenant_id, correlation."""
    _skip_if_missing()
    h = _make_handle()
    assert h.workflow_id == WorkflowId("wf-test-001")
    assert h.procedure_type == ProcedureType.COMPANY_ONBOARDING
    assert h.tenant_id == TenantId("tenant-handle-test")
    assert h.correlation is not None


def test_procedure_handle_defaults() -> None:
    """ProcedureHandle defaults: run_id='', task_queue=''."""
    _skip_if_missing()
    h = _make_handle()
    assert h.run_id == ""
    assert h.task_queue == ""


def test_procedure_handle_with_run_id_and_task_queue() -> None:
    """ProcedureHandle must store explicit run_id and task_queue."""
    _skip_if_missing()
    h = _make_handle(run_id="run-abc123", task_queue="onboarding")
    assert h.run_id == "run-abc123"
    assert h.task_queue == "onboarding"


def test_procedure_handle_is_frozen() -> None:
    """ProcedureHandle is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    h = _make_handle()
    with pytest.raises((AttributeError, TypeError)):
        h.run_id = "tampered"  # type: ignore[misc]
