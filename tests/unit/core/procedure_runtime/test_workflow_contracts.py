"""
tests/unit/core/procedure_runtime/test_workflow_contracts.py
Unit tests for procedure_runtime/workflow_contracts.py.

Covers:
  - ProcedureStatus enum members and string values
  - ManualReviewState enum members
  - ProcedureState: default fields, frozen immutability
  - ProcedureInput: required fields, optional defaults, frozen
  - ProcedureResult: required fields, optional defaults, frozen
  - ProcedureSnapshot: composite of handle, state, input; optional result/version_marker

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
    from dataspace_control_plane_core.procedure_runtime.workflow_contracts import (
        ManualReviewState,
        ProcedureInput,
        ProcedureResult,
        ProcedureSnapshot,
        ProcedureState,
        ProcedureStatus,
        ProcedureVersionMarker,
    )
    from dataspace_control_plane_core.procedure_runtime.procedure_ids import (
        ProcedureHandle,
        ProcedureType,
    )
    from dataspace_control_plane_core.procedure_runtime.progress import ProcedureProgress
    from dataspace_control_plane_core.domains._shared.actor import ActorRef, ActorType
    from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
    from dataspace_control_plane_core.domains._shared.ids import TenantId, WorkflowId
    _AVAILABLE = True
except ImportError as _e:
    _AVAILABLE = False
    _IMPORT_ERROR = str(_e)


def _skip_if_missing() -> None:
    if not _AVAILABLE:
        pytest.skip(f"procedure_runtime.workflow_contracts not available: {_IMPORT_ERROR}")


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _tenant() -> TenantId:
    return TenantId("wf-test-tenant")


def _actor() -> ActorRef:
    return ActorRef(subject="test-svc", actor_type=ActorType.SERVICE)


def _correlation() -> CorrelationContext:
    return CorrelationContext.new()


def _workflow_id() -> WorkflowId:
    return WorkflowId("wf-test-001")


def _handle() -> ProcedureHandle:
    return ProcedureHandle(
        workflow_id=_workflow_id(),
        procedure_type=ProcedureType.COMPANY_ONBOARDING,
        tenant_id=_tenant(),
        correlation=_correlation(),
    )


def _procedure_input(**overrides) -> ProcedureInput:
    defaults: dict = dict(
        tenant_id=_tenant(),
        procedure_type=ProcedureType.COMPANY_ONBOARDING,
        actor=_actor(),
        correlation=_correlation(),
    )
    defaults.update(overrides)
    return ProcedureInput(**defaults)


# ── ProcedureStatus ───────────────────────────────────────────────────────────


def test_procedure_status_all_expected_members_present() -> None:
    """ProcedureStatus must contain all documented states."""
    _skip_if_missing()
    expected = {
        "PENDING", "RUNNING", "PAUSED", "WAITING_FOR_APPROVAL",
        "COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT",
    }
    actual = {m.name for m in ProcedureStatus}
    missing = expected - actual
    assert not missing, f"ProcedureStatus missing: {missing}"


@pytest.mark.parametrize(
    "name, value",
    [
        ("PENDING", "pending"),
        ("RUNNING", "running"),
        ("COMPLETED", "completed"),
        ("FAILED", "failed"),
        ("CANCELLED", "cancelled"),
        ("TIMED_OUT", "timed_out"),
    ],
)
def test_procedure_status_string_values(name: str, value: str) -> None:
    """ProcedureStatus string values must match documented lowercase slugs."""
    _skip_if_missing()
    assert ProcedureStatus[name].value == value


# ── ManualReviewState ─────────────────────────────────────────────────────────


def test_manual_review_state_expected_members() -> None:
    """ManualReviewState must include NOT_REQUIRED, PENDING, APPROVED, REJECTED."""
    _skip_if_missing()
    expected = {"NOT_REQUIRED", "PENDING", "APPROVED", "REJECTED"}
    actual = {m.name for m in ManualReviewState}
    assert expected.issubset(actual)


# ── ProcedureState ────────────────────────────────────────────────────────────


def test_procedure_state_stores_status() -> None:
    """ProcedureState must store the provided status."""
    _skip_if_missing()
    ps = ProcedureState(status=ProcedureStatus.RUNNING)
    assert ps.status == ProcedureStatus.RUNNING


def test_procedure_state_defaults() -> None:
    """ProcedureState must default manual_review to NOT_REQUIRED, attempt=1, message=''."""
    _skip_if_missing()
    ps = ProcedureState(status=ProcedureStatus.PENDING)
    assert ps.manual_review == ManualReviewState.NOT_REQUIRED
    assert ps.attempt == 1
    assert ps.message == ""
    assert ps.progress is not None  # a ProcedureProgress default


def test_procedure_state_is_frozen() -> None:
    """ProcedureState is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    ps = ProcedureState(status=ProcedureStatus.PENDING)
    with pytest.raises((AttributeError, TypeError)):
        ps.status = ProcedureStatus.FAILED  # type: ignore[misc]


# ── ProcedureInput ────────────────────────────────────────────────────────────


def test_procedure_input_stores_required_fields() -> None:
    """ProcedureInput must store tenant_id, procedure_type, actor, correlation."""
    _skip_if_missing()
    inp = _procedure_input()
    assert inp.tenant_id == _tenant()
    assert inp.procedure_type == ProcedureType.COMPANY_ONBOARDING
    assert inp.actor.subject == "test-svc"
    assert inp.correlation is not None


def test_procedure_input_default_payload_is_empty_dict() -> None:
    """ProcedureInput defaults payload to an empty dict."""
    _skip_if_missing()
    inp = _procedure_input()
    assert inp.payload == {}


def test_procedure_input_with_explicit_payload() -> None:
    """ProcedureInput stores an explicit payload dict."""
    _skip_if_missing()
    inp = _procedure_input(payload={"legal_entity_id": "BPN001", "bpnl": "BPNL000001"})
    assert inp.payload["legal_entity_id"] == "BPN001"


def test_procedure_input_default_optional_fields() -> None:
    """ProcedureInput optional fields default to their empty/None values."""
    _skip_if_missing()
    inp = _procedure_input()
    assert inp.legal_entity_id is None
    assert inp.idempotency_key == ""
    assert inp.pack_ids == ()
    assert inp.due_at is None
    assert inp.expires_at is None


def test_procedure_input_is_frozen() -> None:
    """ProcedureInput is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    inp = _procedure_input()
    with pytest.raises((AttributeError, TypeError)):
        inp.idempotency_key = "tampered"  # type: ignore[misc]


# ── ProcedureResult ───────────────────────────────────────────────────────────


def test_procedure_result_stores_required_fields() -> None:
    """ProcedureResult must store workflow_id and status."""
    _skip_if_missing()
    r = ProcedureResult(workflow_id=_workflow_id(), status=ProcedureStatus.COMPLETED)
    assert r.workflow_id == _workflow_id()
    assert r.status == ProcedureStatus.COMPLETED


def test_procedure_result_defaults() -> None:
    """ProcedureResult defaults: output={}, error_code='', error_message='', completed_at=None."""
    _skip_if_missing()
    r = ProcedureResult(workflow_id=_workflow_id(), status=ProcedureStatus.FAILED)
    assert r.output == {}
    assert r.error_code == ""
    assert r.error_message == ""
    assert r.completed_at is None


def test_procedure_result_with_output_dict() -> None:
    """ProcedureResult stores the provided output dict."""
    _skip_if_missing()
    r = ProcedureResult(
        workflow_id=_workflow_id(),
        status=ProcedureStatus.COMPLETED,
        output={"agreement_id": "agr-001"},
    )
    assert r.output["agreement_id"] == "agr-001"


def test_procedure_result_is_frozen() -> None:
    """ProcedureResult is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    r = ProcedureResult(workflow_id=_workflow_id(), status=ProcedureStatus.COMPLETED)
    with pytest.raises((AttributeError, TypeError)):
        r.error_code = "tampered"  # type: ignore[misc]


# ── ProcedureSnapshot ─────────────────────────────────────────────────────────


def test_procedure_snapshot_stores_handle_state_input() -> None:
    """ProcedureSnapshot must hold handle, state, and input."""
    _skip_if_missing()
    h = _handle()
    state = ProcedureState(status=ProcedureStatus.RUNNING)
    inp = _procedure_input()
    snap = ProcedureSnapshot(handle=h, state=state, input=inp)
    assert snap.handle is h
    assert snap.state is state
    assert snap.input is inp


def test_procedure_snapshot_optional_result_and_version_marker_default_to_none() -> None:
    """ProcedureSnapshot result and version_marker default to None."""
    _skip_if_missing()
    snap = ProcedureSnapshot(
        handle=_handle(),
        state=ProcedureState(status=ProcedureStatus.PENDING),
        input=_procedure_input(),
    )
    assert snap.result is None
    assert snap.version_marker is None


def test_procedure_snapshot_with_result() -> None:
    """ProcedureSnapshot stores the provided result."""
    _skip_if_missing()
    result = ProcedureResult(workflow_id=_workflow_id(), status=ProcedureStatus.COMPLETED)
    snap = ProcedureSnapshot(
        handle=_handle(),
        state=ProcedureState(status=ProcedureStatus.COMPLETED),
        input=_procedure_input(),
        result=result,
    )
    assert snap.result is result


def test_procedure_snapshot_is_frozen() -> None:
    """ProcedureSnapshot is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    snap = ProcedureSnapshot(
        handle=_handle(),
        state=ProcedureState(status=ProcedureStatus.PENDING),
        input=_procedure_input(),
    )
    with pytest.raises((AttributeError, TypeError)):
        snap.result = None  # type: ignore[misc]


# ── ProcedureVersionMarker ────────────────────────────────────────────────────


def test_procedure_version_marker_stores_version_and_reason() -> None:
    """ProcedureVersionMarker must store version and optional reason."""
    _skip_if_missing()
    vm = ProcedureVersionMarker(version="v2", reason="activity renamed")
    assert vm.version == "v2"
    assert vm.reason == "activity renamed"


def test_procedure_version_marker_default_reason_is_empty() -> None:
    """ProcedureVersionMarker reason defaults to empty string."""
    _skip_if_missing()
    vm = ProcedureVersionMarker(version="v1")
    assert vm.reason == ""
