from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.api.deps.auth import get_current_principal
from app.api.deps.resources import (
    get_procedure_catalog,
    maybe_get_database_pool,
    maybe_get_temporal_gateway,
)
from app.api.schemas.streams import StreamTicketRequest
from app.auth.principals import Principal
from app.main import create_app
from app.services.procedure_catalog import ProcedureCatalog
from app.settings import settings


def _principal() -> Principal:
    return Principal(
        subject="user-1",
        email="user@example.com",
        realm_roles=frozenset(),
        client_roles=frozenset(),
        tenant_ids=frozenset({"tenant-a"}),
    )


class _FakeGateway:
    async def describe_workflow(self, workflow_id: str):
        return SimpleNamespace(
            id=workflow_id,
            run_id="run-1",
            workflow_type="CompanyOnboardingWorkflow",
            status=SimpleNamespace(name="RUNNING"),
            start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
            close_time=None,
            search_attributes={
                "tenant_id": ["tenant-a"],
                "procedure_type": ["company-onboarding"],
                "status": ["running"],
            },
        )

    async def query_workflow(self, workflow_id: str, query_name: str):
        assert query_name == "get_status"
        return {
            "status": "running",
            "phase": "awaiting_approval",
            "blocking_reason": "awaiting operator approval",
            "external_refs": {"registration_ref": "reg:tenant-a:lei-1"},
            "next_required_action": "approve",
            "is_complete": False,
            "progress_percent": 40,
        }


def _client() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_principal] = _principal
    app.dependency_overrides[get_procedure_catalog] = ProcedureCatalog.discover
    app.dependency_overrides[maybe_get_temporal_gateway] = _FakeGateway
    app.dependency_overrides[maybe_get_database_pool] = lambda: None
    return TestClient(app, raise_server_exceptions=False)


def test_webhook_routes_are_not_mounted_without_secret(monkeypatch) -> None:
    monkeypatch.setattr(settings, "webhook_shared_secret", None)
    client = TestClient(create_app(), raise_server_exceptions=False)

    response = client.post("/api/v1/webhooks/management")

    assert response.status_code == 404


def test_stream_ticket_is_scoped_to_one_workflow() -> None:
    client = _client()

    issue_response = client.post(
        "/api/v1/streams/tickets",
        headers={"Authorization": "Bearer fake-token"},
        json=StreamTicketRequest(workflow_id="wf-1").model_dump(),
    )
    assert issue_response.status_code == 200
    ticket = issue_response.json()["ticket"]

    denied = client.get(f"/api/v1/streams/workflows/wf-2?ticket={ticket}")
    assert denied.status_code == 401
