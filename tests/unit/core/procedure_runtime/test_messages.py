"""
tests/unit/core/procedure_runtime/test_messages.py
Unit tests for procedure_runtime/messages.py — typed procedure control messages.

Covers:
  - CancelProcedure: required fields and frozen immutability
  - ApproveProcedure: required fields, optional comment, frozen
  - RejectProcedure: required fields, frozen
  - RetryProcedure: optional reason defaults to empty string
  - PauseProcedure: optional reason defaults to empty string
  - ResumeProcedure: optional reason defaults to empty string
  - ProcedureQuery: required fields, optional include_payload
  - ProcedureQueryResponse: snapshot field and optional metadata

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
    from dataspace_control_plane_core.procedure_runtime.messages import (
        ApproveProcedure,
        CancelProcedure,
        PauseProcedure,
        ProcedureQuery,
        ProcedureQueryResponse,
        RejectProcedure,
        ResumeProcedure,
        RetryProcedure,
    )
    from dataspace_control_plane_core.procedure_runtime.workflow_contracts import (
        ProcedureInput,
        ProcedureSnapshot,
        ProcedureState,
        ProcedureStatus,
    )
    from dataspace_control_plane_core.procedure_runtime.procedure_ids import (
        ProcedureHandle,
        ProcedureType,
    )
    from dataspace_control_plane_core.domains._shared.actor import ActorRef, ActorType
    from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
    from dataspace_control_plane_core.domains._shared.ids import TenantId, WorkflowId
    _AVAILABLE = True
except ImportError as _e:
    _AVAILABLE = False
    _IMPORT_ERROR = str(_e)


def _skip_if_missing() -> None:
    if not _AVAILABLE:
        pytest.skip(f"procedure_runtime.messages not available: {_IMPORT_ERROR}")


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _tenant() -> TenantId:
    return TenantId("msg-test-tenant")


def _wf_id() -> WorkflowId:
    return WorkflowId("wf-msg-001")


def _actor() -> ActorRef:
    return ActorRef(subject="operator@example.com", actor_type=ActorType.HUMAN)


def _correlation() -> CorrelationContext:
    return CorrelationContext.new()


def _snapshot() -> ProcedureSnapshot:
    return ProcedureSnapshot(
        handle=ProcedureHandle(
            workflow_id=_wf_id(),
            procedure_type=ProcedureType.COMPANY_ONBOARDING,
            tenant_id=_tenant(),
            correlation=_correlation(),
        ),
        state=ProcedureState(status=ProcedureStatus.RUNNING),
        input=ProcedureInput(
            tenant_id=_tenant(),
            procedure_type=ProcedureType.COMPANY_ONBOARDING,
            actor=_actor(),
            correlation=_correlation(),
        ),
    )


# ── CancelProcedure ───────────────────────────────────────────────────────────


def test_cancel_procedure_stores_all_fields() -> None:
    """CancelProcedure must store tenant_id, workflow_id, actor, correlation, reason."""
    _skip_if_missing()
    msg = CancelProcedure(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        actor=_actor(),
        correlation=_correlation(),
        reason="operator cancelled",
    )
    assert msg.tenant_id == _tenant()
    assert msg.workflow_id == _wf_id()
    assert msg.reason == "operator cancelled"


def test_cancel_procedure_is_frozen() -> None:
    """CancelProcedure is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    msg = CancelProcedure(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        actor=_actor(),
        correlation=_correlation(),
        reason="test",
    )
    with pytest.raises((AttributeError, TypeError)):
        msg.reason = "tampered"  # type: ignore[misc]


# ── ApproveProcedure ──────────────────────────────────────────────────────────


def test_approve_procedure_stores_required_fields() -> None:
    """ApproveProcedure must store tenant_id, workflow_id, actor, correlation."""
    _skip_if_missing()
    msg = ApproveProcedure(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        actor=_actor(),
        correlation=_correlation(),
    )
    assert msg.workflow_id == _wf_id()


def test_approve_procedure_comment_defaults_to_empty() -> None:
    """ApproveProcedure comment defaults to empty string."""
    _skip_if_missing()
    msg = ApproveProcedure(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        actor=_actor(),
        correlation=_correlation(),
    )
    assert msg.comment == ""


def test_approve_procedure_with_explicit_comment() -> None:
    """ApproveProcedure stores an explicit comment."""
    _skip_if_missing()
    msg = ApproveProcedure(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        actor=_actor(),
        correlation=_correlation(),
        comment="Looks good",
    )
    assert msg.comment == "Looks good"


def test_approve_procedure_is_frozen() -> None:
    """ApproveProcedure is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    msg = ApproveProcedure(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        actor=_actor(),
        correlation=_correlation(),
    )
    with pytest.raises((AttributeError, TypeError)):
        msg.comment = "tampered"  # type: ignore[misc]


# ── RejectProcedure ───────────────────────────────────────────────────────────


def test_reject_procedure_stores_reason() -> None:
    """RejectProcedure must store the reason."""
    _skip_if_missing()
    msg = RejectProcedure(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        actor=_actor(),
        correlation=_correlation(),
        reason="compliance failure",
    )
    assert msg.reason == "compliance failure"


def test_reject_procedure_is_frozen() -> None:
    """RejectProcedure is frozen — mutation must raise."""
    _skip_if_missing()
    msg = RejectProcedure(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        actor=_actor(),
        correlation=_correlation(),
        reason="test",
    )
    with pytest.raises((AttributeError, TypeError)):
        msg.reason = "tampered"  # type: ignore[misc]


# ── RetryProcedure ────────────────────────────────────────────────────────────


def test_retry_procedure_reason_defaults_to_empty() -> None:
    """RetryProcedure reason defaults to empty string."""
    _skip_if_missing()
    msg = RetryProcedure(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        actor=_actor(),
        correlation=_correlation(),
    )
    assert msg.reason == ""


# ── PauseProcedure ────────────────────────────────────────────────────────────


def test_pause_procedure_reason_defaults_to_empty() -> None:
    """PauseProcedure reason defaults to empty string."""
    _skip_if_missing()
    msg = PauseProcedure(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        actor=_actor(),
        correlation=_correlation(),
    )
    assert msg.reason == ""


# ── ResumeProcedure ───────────────────────────────────────────────────────────


def test_resume_procedure_reason_defaults_to_empty() -> None:
    """ResumeProcedure reason defaults to empty string."""
    _skip_if_missing()
    msg = ResumeProcedure(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        actor=_actor(),
        correlation=_correlation(),
    )
    assert msg.reason == ""


# ── ProcedureQuery ────────────────────────────────────────────────────────────


def test_procedure_query_stores_fields() -> None:
    """ProcedureQuery must store tenant_id, workflow_id, correlation."""
    _skip_if_missing()
    q = ProcedureQuery(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        correlation=_correlation(),
    )
    assert q.tenant_id == _tenant()
    assert q.workflow_id == _wf_id()


def test_procedure_query_include_payload_defaults_to_false() -> None:
    """ProcedureQuery.include_payload defaults to False."""
    _skip_if_missing()
    q = ProcedureQuery(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        correlation=_correlation(),
    )
    assert q.include_payload is False


def test_procedure_query_is_frozen() -> None:
    """ProcedureQuery is frozen — mutation must raise."""
    _skip_if_missing()
    q = ProcedureQuery(
        tenant_id=_tenant(),
        workflow_id=_wf_id(),
        correlation=_correlation(),
    )
    with pytest.raises((AttributeError, TypeError)):
        q.include_payload = True  # type: ignore[misc]


# ── ProcedureQueryResponse ────────────────────────────────────────────────────


def test_procedure_query_response_stores_snapshot() -> None:
    """ProcedureQueryResponse must store the provided snapshot."""
    _skip_if_missing()
    snap = _snapshot()
    resp = ProcedureQueryResponse(snapshot=snap)
    assert resp.snapshot is snap


def test_procedure_query_response_metadata_defaults_to_empty_dict() -> None:
    """ProcedureQueryResponse metadata defaults to empty dict."""
    _skip_if_missing()
    resp = ProcedureQueryResponse(snapshot=_snapshot())
    assert resp.metadata == {}


def test_procedure_query_response_with_metadata() -> None:
    """ProcedureQueryResponse stores explicit metadata."""
    _skip_if_missing()
    resp = ProcedureQueryResponse(
        snapshot=_snapshot(),
        metadata={"source": "temporal"},
    )
    assert resp.metadata["source"] == "temporal"
