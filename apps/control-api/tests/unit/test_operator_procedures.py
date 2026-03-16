from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient

from dataspace_control_plane_adapters.infrastructure.temporal_client.errors import (
    WorkflowAlreadyStartedError,
)

from app.api.deps.auth import get_current_principal
from app.api.deps.resources import get_start_procedure_service
from app.application.dto.procedures import ProcedureHandleDTO
from app.auth.principals import Principal
from app.main import create_app


def _principal() -> Principal:
    return Principal(
        subject="operator-1",
        email="ops@example.com",
        realm_roles=frozenset({"dataspace-admin"}),
        tenant_ids=frozenset({"tenant-a"}),
    )


@dataclass
class _FakeStartProcedureService:
    result: ProcedureHandleDTO | None = None
    error: Exception | None = None

    async def start(self, **_: object) -> ProcedureHandleDTO:
        if self.error is not None:
            raise self.error
        assert self.result is not None
        return self.result


def _client_with_service(service: _FakeStartProcedureService) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_current_principal] = _principal
    app.dependency_overrides[get_start_procedure_service] = lambda: service
    return TestClient(app, raise_server_exceptions=False)


def _request_payload() -> dict:
    return {
        "procedure_type": "company-onboarding",
        "tenant_id": "tenant-a",
        "legal_entity_id": "lei-1",
        "payload": {
            "legal_entity_name": "ACME GmbH",
            "bpnl": "BPNL000000000001",
            "jurisdiction": "DE",
            "contact_email": "ops@example.com",
            "connector_url": "https://connector.example.com",
        },
    }


def test_operator_start_procedure_returns_handle() -> None:
    client = _client_with_service(
        _FakeStartProcedureService(
            result=ProcedureHandleDTO(
                workflow_id="company-onboarding:tenant-a:lei-1",
                procedure_type="company-onboarding",
                tenant_id="tenant-a",
                status="running",
                poll_url="/api/v1/operator/procedures/company-onboarding:tenant-a:lei-1",
                stream_url="/api/v1/streams/workflows/company-onboarding:tenant-a:lei-1",
                correlation_id="corr-1",
            )
        )
    )

    response = client.post(
        "/api/v1/operator/procedures/start",
        headers={"Authorization": "Bearer fake-token"},
        json=_request_payload(),
    )

    assert response.status_code == 202
    assert response.json()["status"] == "running"


def test_operator_start_procedure_returns_422_for_invalid_payload() -> None:
    client = _client_with_service(
        _FakeStartProcedureService(error=ValueError("Unexpected payload field(s) for procedure"))
    )

    response = client.post(
        "/api/v1/operator/procedures/start",
        headers={"Authorization": "Bearer fake-token"},
        json=_request_payload(),
    )

    assert response.status_code == 422


def test_operator_start_procedure_returns_409_for_duplicate_business_key() -> None:
    client = _client_with_service(
        _FakeStartProcedureService(
            error=WorkflowAlreadyStartedError("company-onboarding:tenant-a:lei-1")
        )
    )

    response = client.post(
        "/api/v1/operator/procedures/start",
        headers={"Authorization": "Bearer fake-token"},
        json=_request_payload(),
    )

    assert response.status_code == 409
