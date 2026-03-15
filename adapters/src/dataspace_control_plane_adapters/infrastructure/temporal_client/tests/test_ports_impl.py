from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from dataspace_control_plane_adapters._shared.health import HealthStatus
from dataspace_control_plane_adapters.infrastructure.temporal_client.health import (
    TemporalHealthProbe,
)
from dataspace_control_plane_adapters.infrastructure.temporal_client import ports_impl as temporal_ports
from dataspace_control_plane_adapters.infrastructure.temporal_client.config import (
    TemporalClientSettings,
)
from dataspace_control_plane_core.domains._shared.actor import ActorRef, ActorType
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from dataspace_control_plane_core.domains._shared.ids import TenantId, WorkflowId
from dataspace_control_plane_core.procedure_runtime.messages import (
    ApproveProcedure,
    CancelProcedure,
    PauseProcedure,
    ProcedureQuery,
    RejectProcedure,
    ResumeProcedure,
    RetryProcedure,
)
from dataspace_control_plane_core.procedure_runtime.workflow_contracts import (
    ManualReviewState,
    ProcedureStatus,
)


def _settings() -> TemporalClientSettings:
    return TemporalClientSettings(
        host="temporal.example.com",
        port=7233,
        namespace="dataspace",
        default_task_queue="dataspace-control-plane",
    )


def _tenant_id() -> TenantId:
    return TenantId("tenant-a")


def _workflow_id() -> WorkflowId:
    return WorkflowId("company-onboarding:workflow-1")


def _correlation() -> CorrelationContext:
    return CorrelationContext.new(workflow_id=_workflow_id())


def _actor() -> ActorRef:
    return ActorRef(
        subject="operator-1",
        actor_type=ActorType.HUMAN,
        tenant_id=_tenant_id(),
        display_name="Operator One",
    )


@dataclass(frozen=True)
class _StatusQuery:
    phase: str
    blocking_reason: str
    next_required_action: str
    is_complete: bool


class _FakeWorkflowHandleHelper:
    def __init__(self, _client: object) -> None:
        self.cancelled: list[str] = []

    async def cancel(self, workflow_id: str) -> None:
        self.cancelled.append(workflow_id)

    async def describe(self, workflow_id: str) -> dict[str, object]:
        return {
            "workflow_id": workflow_id,
            "run_id": "run-1",
            "workflow_type": "CompanyOnboardingWorkflow",
            "status": "RUNNING",
            "close_time": datetime(2025, 1, 1, tzinfo=timezone.utc).isoformat(),
            "task_queue": "dataspace-control-plane",
        }


class _FakeSignalSender:
    def __init__(self, _client: object) -> None:
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    async def send(self, workflow_id: str, signal: str, payload: dict[str, object]) -> None:
        self.calls.append((workflow_id, signal, payload))


class _FakeQueryExecutor:
    def __init__(self, _client: object) -> None:
        self.calls: list[tuple[str, str]] = []

    async def execute(self, workflow_id: str, query_name: str) -> _StatusQuery:
        self.calls.append((workflow_id, query_name))
        return _StatusQuery(
            phase="awaiting_approval",
            blocking_reason="operator approval required",
            next_required_action="approve",
            is_complete=False,
        )


class _FakeUpdateExecutor:
    def __init__(self, _client: object) -> None:
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    async def send(self, workflow_id: str, update_name: str, payload: dict[str, object]) -> None:
        self.calls.append((workflow_id, update_name, payload))


@pytest.mark.asyncio
async def test_temporal_gateway_exposes_full_control_surface(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(temporal_ports, "WorkflowHandleHelper", _FakeWorkflowHandleHelper)
    monkeypatch.setattr(temporal_ports, "SignalSender", _FakeSignalSender)
    monkeypatch.setattr(temporal_ports, "QueryExecutor", _FakeQueryExecutor)
    monkeypatch.setattr(temporal_ports, "UpdateExecutor", _FakeUpdateExecutor)

    gateway = temporal_ports.TemporalWorkflowGateway(object())

    await gateway.approve(
        ApproveProcedure(_tenant_id(), _workflow_id(), _actor(), _correlation(), "looks good")
    )
    await gateway.reject(
        RejectProcedure(_tenant_id(), _workflow_id(), _actor(), _correlation(), "not yet")
    )
    await gateway.pause(
        PauseProcedure(_tenant_id(), _workflow_id(), _actor(), _correlation(), "hold")
    )
    await gateway.resume(
        ResumeProcedure(_tenant_id(), _workflow_id(), _actor(), _correlation(), "continue")
    )
    await gateway.retry(
        RetryProcedure(_tenant_id(), _workflow_id(), _actor(), _correlation(), "rerun")
    )
    await gateway.cancel(
        CancelProcedure(_tenant_id(), _workflow_id(), _actor(), _correlation(), "stop")
    )

    assert [name for _, name, _ in gateway._update_executor.calls] == [
        "approve",
        "reject",
        "pause",
        "resume",
        "retry",
    ]
    assert gateway._helper.cancelled == [str(_workflow_id())]


@pytest.mark.asyncio
async def test_temporal_query_normalizes_status_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(temporal_ports, "WorkflowHandleHelper", _FakeWorkflowHandleHelper)
    monkeypatch.setattr(temporal_ports, "SignalSender", _FakeSignalSender)
    monkeypatch.setattr(temporal_ports, "QueryExecutor", _FakeQueryExecutor)
    monkeypatch.setattr(temporal_ports, "UpdateExecutor", _FakeUpdateExecutor)

    gateway = temporal_ports.TemporalWorkflowGateway(object())
    response = await gateway.query(
        ProcedureQuery(
            tenant_id=_tenant_id(),
            workflow_id=_workflow_id(),
            correlation=_correlation(),
            include_payload=True,
        )
    )

    assert response.snapshot.state.status is ProcedureStatus.WAITING_FOR_APPROVAL
    assert response.snapshot.state.manual_review is ManualReviewState.PENDING
    assert response.snapshot.input.payload["phase"] == "awaiting_approval"
    assert response.metadata["query_name"] == "get_status"


@pytest.mark.asyncio
async def test_temporal_health_probe_exposes_runtime_capabilities() -> None:
    probe = TemporalHealthProbe(_settings())

    report = await probe.check()
    descriptor = probe.capability_descriptor()

    assert report.status is HealthStatus.OK
    assert "updates" in descriptor["capabilities"]


# ---------------------------------------------------------------------------
# _map_temporal_status — exhaustive status mapping coverage
# ---------------------------------------------------------------------------

def test_map_temporal_status_maps_all_known_variants() -> None:
    from dataspace_control_plane_adapters.infrastructure.temporal_client.ports_impl import (
        _map_temporal_status,
    )
    from dataspace_control_plane_core.procedure_runtime.workflow_contracts import ProcedureStatus

    assert _map_temporal_status("RUNNING") is ProcedureStatus.RUNNING
    assert _map_temporal_status("COMPLETED") is ProcedureStatus.COMPLETED
    assert _map_temporal_status("FAILED") is ProcedureStatus.FAILED
    assert _map_temporal_status("CANCELED") is ProcedureStatus.CANCELLED
    assert _map_temporal_status("TIMED_OUT") is ProcedureStatus.TIMED_OUT
    assert _map_temporal_status("WORKFLOW_EXECUTION_STATUS_RUNNING") is ProcedureStatus.RUNNING
    assert _map_temporal_status("WORKFLOW_EXECUTION_STATUS_COMPLETED") is ProcedureStatus.COMPLETED
    # Unknown status string falls back to PENDING
    assert _map_temporal_status("TOTALLY_UNKNOWN") is ProcedureStatus.PENDING


# ---------------------------------------------------------------------------
# _infer_procedure_type — prefix fallback and error path
# ---------------------------------------------------------------------------

def test_infer_procedure_type_uses_prefix_fallback_when_no_workflow_type() -> None:
    from dataspace_control_plane_adapters.infrastructure.temporal_client.ports_impl import (
        _infer_procedure_type,
    )

    assert _infer_procedure_type(None, "company-onboarding:wf-1") == "company-onboarding"
    assert _infer_procedure_type(None, "contract:wf-2") == "contract-negotiation"
    assert _infer_procedure_type(None, "dpp:wf-3") == "asset-twin-publication"


def test_infer_procedure_type_raises_for_completely_unknown_type() -> None:
    from dataspace_control_plane_adapters.infrastructure.temporal_client.ports_impl import (
        _infer_procedure_type,
    )
    from dataspace_control_plane_adapters.infrastructure.temporal_client.errors import (
        TemporalRpcError,
    )

    with pytest.raises(TemporalRpcError):
        _infer_procedure_type(None, "totally-unknown-workflow-id")


# ---------------------------------------------------------------------------
# _resolve_status — is_paused and manual_review.decision branches
# ---------------------------------------------------------------------------

def test_resolve_status_returns_paused_when_is_paused_flag_set() -> None:
    from dataspace_control_plane_adapters.infrastructure.temporal_client.ports_impl import (
        _resolve_status,
    )
    from dataspace_control_plane_core.procedure_runtime.workflow_contracts import ProcedureStatus

    status = _resolve_status("RUNNING", {"is_paused": True, "blocking_reason": ""})
    assert status is ProcedureStatus.PAUSED


def test_resolve_status_maps_rejected_manual_review_to_failed() -> None:
    from dataspace_control_plane_adapters.infrastructure.temporal_client.ports_impl import (
        _resolve_status,
    )
    from dataspace_control_plane_core.procedure_runtime.workflow_contracts import ProcedureStatus

    status = _resolve_status(
        "RUNNING",
        {"is_paused": False, "manual_review": {"is_pending": False, "decision": "Rejected"}},
    )
    assert status is ProcedureStatus.FAILED


# ---------------------------------------------------------------------------
# _normalize_query_result — dataclass serialization path
# ---------------------------------------------------------------------------

def test_normalize_query_result_converts_dataclass_to_dict() -> None:
    from dataspace_control_plane_adapters.infrastructure.temporal_client.ports_impl import (
        _normalize_query_result,
    )
    from dataclasses import dataclass

    @dataclass
    class _SampleQuery:
        phase: str
        is_complete: bool

    result = _normalize_query_result(_SampleQuery(phase="running", is_complete=False))
    assert result == {"phase": "running", "is_complete": False}


# ---------------------------------------------------------------------------
# _parse_iso_datetime — invalid input returns None
# ---------------------------------------------------------------------------

def test_parse_iso_datetime_returns_none_for_invalid_string() -> None:
    from dataspace_control_plane_adapters.infrastructure.temporal_client.ports_impl import (
        _parse_iso_datetime,
    )

    assert _parse_iso_datetime("not-a-date") is None
    assert _parse_iso_datetime(None) is None
    assert _parse_iso_datetime("") is None


# ---------------------------------------------------------------------------
# TemporalWorkflowGateway — custom control_names override
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_gateway_uses_custom_control_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(temporal_ports, "WorkflowHandleHelper", _FakeWorkflowHandleHelper)
    monkeypatch.setattr(temporal_ports, "SignalSender", _FakeSignalSender)
    monkeypatch.setattr(temporal_ports, "QueryExecutor", _FakeQueryExecutor)
    monkeypatch.setattr(temporal_ports, "UpdateExecutor", _FakeUpdateExecutor)

    gateway = temporal_ports.TemporalWorkflowGateway(
        object(),
        control_names={"approve": "my_approve", "query": "my_status"},
    )

    await gateway.approve(
        ApproveProcedure(_tenant_id(), _workflow_id(), _actor(), _correlation(), "ok")
    )

    assert gateway._update_executor.calls[0][1] == "my_approve"
    assert gateway._control_names["query"] == "my_status"
