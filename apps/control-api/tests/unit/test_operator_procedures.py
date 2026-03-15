from types import SimpleNamespace

import pytest

from app.api.routers.operator.procedures import StartProcedureRequest, start_procedure
from app.auth.principals import Principal
from app.services.idempotency import IdempotencyStore
from app.services.procedure_catalog import ProcedureCatalog


class _FakeHandle:
    def __init__(self, workflow_id: str) -> None:
        self.id = workflow_id


class _FakeGateway:
    def __init__(self) -> None:
        self.calls = 0

    async def start_procedure(self, command, catalog):
        self.calls += 1
        return _FakeHandle("wf-123")


@pytest.mark.asyncio
async def test_operator_start_procedure_reuses_cached_result_for_duplicate_idempotency_key():
    request = SimpleNamespace(state=SimpleNamespace(correlation_id="corr-123"))
    gateway = _FakeGateway()
    catalog = ProcedureCatalog.discover()
    store = IdempotencyStore()
    principal = Principal(
        subject="operator-1",
        email="ops@example.com",
        realm_roles=frozenset({"dataspace-admin"}),
        tenant_ids=frozenset({"tenant-a"}),
    )
    body = StartProcedureRequest(
        procedure_type="company-onboarding",
        tenant_id="tenant-a",
        legal_entity_id="lei-1",
        payload={
            "legal_entity_name": "ACME GmbH",
            "bpnl": "BPNL000000000001",
            "jurisdiction": "DE",
            "contact_email": "ops@example.com",
            "connector_url": "https://connector.example.com",
        },
        idempotency_key="idem-123",
    )

    first = await start_procedure(body, request, principal, gateway, catalog, store)
    second = await start_procedure(body, request, principal, gateway, catalog, store)

    assert gateway.calls == 1
    assert first.workflow_id == second.workflow_id == "wf-123"
    assert second.poll_url == "/api/v1/operator/procedures/wf-123"

