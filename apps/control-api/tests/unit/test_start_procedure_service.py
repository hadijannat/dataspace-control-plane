from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from dataspace_control_plane_adapters.infrastructure.postgres.repositories.idempotency_repository import (
    IdempotencyAcquireResult,
    IdempotencyRecord,
)
from dataspace_control_plane_adapters.infrastructure.temporal_client.errors import (
    WorkflowAlreadyStartedError,
)

from app.auth.principals import Principal
from app.services.procedure_catalog import ProcedureCatalog
from app.services.start_procedure_service import (
    IdempotencyConflictError,
    StartProcedureService,
)
from app.services.temporal_gateway import StartedWorkflow


def _principal() -> Principal:
    return Principal(
        subject="operator-1",
        email="ops@example.com",
        realm_roles=frozenset({"dataspace-admin"}),
        client_roles=frozenset(),
        tenant_ids=frozenset({"tenant-a"}),
    )


def _request_payload(**overrides: str) -> dict[str, str]:
    payload = {
        "legal_entity_name": "ACME GmbH",
        "bpnl": "BPNL000000000001",
        "jurisdiction": "DE",
        "contact_email": "ops@example.com",
        "connector_url": "https://connector.example.com",
    }
    payload.update(overrides)
    return payload


@dataclass
class _FakeIdempotencyRepository:
    records: dict[tuple[str, str, str], IdempotencyRecord]

    def __init__(self) -> None:
        self.records = {}

    async def acquire(self, **kwargs) -> IdempotencyAcquireResult:
        key = (kwargs["tenant_id"], kwargs["procedure_type"], kwargs["idempotency_key"])
        existing = self.records.get(key)
        if existing is None:
            record = IdempotencyRecord(
                tenant_id=kwargs["tenant_id"],
                procedure_type=kwargs["procedure_type"],
                idempotency_key=kwargs["idempotency_key"],
                request_fingerprint=kwargs["request_fingerprint"],
                workflow_id=kwargs["workflow_id"],
                run_id=None,
                response_json=kwargs["response_json"],
                status=kwargs["status"],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            self.records[key] = record
            return IdempotencyAcquireResult(outcome="acquired", record=record)
        if existing.request_fingerprint != kwargs["request_fingerprint"]:
            return IdempotencyAcquireResult(outcome="conflict", record=existing)
        return IdempotencyAcquireResult(outcome="replay", record=existing)

    async def finalize(self, **kwargs) -> None:
        key = (kwargs["tenant_id"], kwargs["procedure_type"], kwargs["idempotency_key"])
        record = self.records[key]
        self.records[key] = IdempotencyRecord(
            tenant_id=record.tenant_id,
            procedure_type=record.procedure_type,
            idempotency_key=record.idempotency_key,
            request_fingerprint=record.request_fingerprint,
            workflow_id=record.workflow_id,
            run_id=kwargs["run_id"],
            response_json=kwargs["response_json"],
            status=kwargs["status"],
            created_at=record.created_at,
            updated_at=datetime.now(timezone.utc),
        )

    async def release(self, **kwargs) -> None:
        key = (kwargs["tenant_id"], kwargs["procedure_type"], kwargs["idempotency_key"])
        self.records.pop(key, None)


@dataclass
class _FakeRuntimeRepository:
    calls: list[dict]

    def __init__(self) -> None:
        self.calls = []

    async def upsert_state(self, **kwargs) -> None:
        self.calls.append(kwargs)


@dataclass
class _FakeAuditSink:
    records: list[object]

    def __init__(self) -> None:
        self.records = []

    async def emit(self, record) -> None:
        self.records.append(record)


@dataclass
class _FakeGateway:
    started: set[str]
    calls: list[dict]

    def __init__(self) -> None:
        self.started = set()
        self.calls = []

    async def start_definition(self, **kwargs) -> StartedWorkflow:
        workflow_id = kwargs["workflow_id"]
        self.calls.append(kwargs)
        if workflow_id in self.started:
            raise WorkflowAlreadyStartedError(workflow_id)
        self.started.add(workflow_id)
        return StartedWorkflow(workflow_id=workflow_id, run_id=f"run:{workflow_id}")


def _service() -> StartProcedureService:
    return StartProcedureService(
        catalog=ProcedureCatalog.discover(),
        gateway=_FakeGateway(),
        idempotency_repository=_FakeIdempotencyRepository(),
        procedure_runtime_repository=_FakeRuntimeRepository(),
        audit_sink=_FakeAuditSink(),
    )


@pytest.mark.asyncio
async def test_start_service_replays_identical_idempotent_request() -> None:
    service = _service()

    first = await service.start(
        procedure_type="company-onboarding",
        tenant_id="tenant-a",
        legal_entity_id="lei-1",
        payload=_request_payload(),
        idempotency_key="idem-1",
        principal=_principal(),
        correlation_id="corr-1",
        poll_url_template="/api/v1/operator/procedures/{workflow_id}",
        audit_event_type="procedure.started",
    )
    second = await service.start(
        procedure_type="company-onboarding",
        tenant_id="tenant-a",
        legal_entity_id="lei-1",
        payload=_request_payload(),
        idempotency_key="idem-1",
        principal=_principal(),
        correlation_id="corr-2",
        poll_url_template="/api/v1/operator/procedures/{workflow_id}",
        audit_event_type="procedure.started",
    )

    assert first.workflow_id == second.workflow_id == "company-onboarding:tenant-a:lei-1"
    assert first.status == second.status == "running"
    assert len(service._gateway.calls) == 1


@pytest.mark.asyncio
async def test_start_service_rejects_scoped_key_reuse_with_different_payload() -> None:
    service = _service()

    await service.start(
        procedure_type="company-onboarding",
        tenant_id="tenant-a",
        legal_entity_id="lei-1",
        payload=_request_payload(),
        idempotency_key="idem-1",
        principal=_principal(),
        correlation_id="corr-1",
        poll_url_template="/api/v1/operator/procedures/{workflow_id}",
        audit_event_type="procedure.started",
    )

    with pytest.raises(IdempotencyConflictError):
        await service.start(
            procedure_type="company-onboarding",
            tenant_id="tenant-a",
            legal_entity_id="lei-1",
            payload=_request_payload(contact_email="different@example.com"),
            idempotency_key="idem-1",
            principal=_principal(),
            correlation_id="corr-2",
            poll_url_template="/api/v1/operator/procedures/{workflow_id}",
            audit_event_type="procedure.started",
        )


@pytest.mark.asyncio
async def test_start_service_rejects_duplicate_onboarding_business_key() -> None:
    service = _service()

    await service.start(
        procedure_type="company-onboarding",
        tenant_id="tenant-a",
        legal_entity_id="lei-1",
        payload=_request_payload(),
        idempotency_key="idem-1",
        principal=_principal(),
        correlation_id="corr-1",
        poll_url_template="/api/v1/operator/procedures/{workflow_id}",
        audit_event_type="procedure.started",
    )

    with pytest.raises(WorkflowAlreadyStartedError):
        await service.start(
            procedure_type="company-onboarding",
            tenant_id="tenant-a",
            legal_entity_id="lei-1",
            payload=_request_payload(),
            idempotency_key="idem-2",
            principal=_principal(),
            correlation_id="corr-2",
            poll_url_template="/api/v1/operator/procedures/{workflow_id}",
            audit_event_type="procedure.started",
        )
