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
