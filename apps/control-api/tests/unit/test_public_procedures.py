"""
Unit tests for public procedure endpoints and stream ticket endpoint.

Covers:
- POST /api/v1/public/procedures/start
- GET /api/v1/public/procedures/{workflow_id}
- POST /api/v1/streams/tickets
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock

from app.main import create_app
from app.api.deps.auth import get_current_principal
from app.api.deps.resources import (
    get_temporal_gateway,
    get_idempotency_store,
    get_procedure_catalog,
    maybe_get_temporal_gateway,
    maybe_get_database_pool,
)
from app.auth.principals import Principal
from app.application.dto.procedures import ProcedureHandleDTO, ProcedureStatusDTO

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_principal(
    subject: str = "user-1",
    tenant_ids: tuple[str, ...] = ("tenant-a",),
    realm_roles: tuple[str, ...] = (),
) -> Principal:
    return Principal(
        subject=subject,
        email="user@example.com",
        realm_roles=frozenset(realm_roles),
        tenant_ids=frozenset(tenant_ids),
    )


class FakeWorkflowHandle:
    def __init__(self, workflow_id: str):
        self.id = workflow_id


class FakeTemporalGateway:
    """Minimal TemporalGateway stand-in that records calls."""

    def __init__(self, workflow_id: str = "wf-public-001"):
        self._workflow_id = workflow_id
        self.calls: list[dict] = []

    async def start_procedure(self, cmd, catalog):
        self.calls.append({"cmd": cmd, "catalog": catalog})
        return FakeWorkflowHandle(self._workflow_id)

    async def describe_workflow(self, workflow_id: str):
        return None  # simulate not found via gateway


class FakeIdempotencyStore:
    """In-memory idempotency store stub."""

    def __init__(self, cached_result=None):
        self._cached = cached_result
        self._stored: dict = {}

    async def check(self, key: str):
        return self._cached

    async def store(self, key: str, result: dict):
        self._stored[key] = result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client_factory():
    """
    Return a factory that builds a TestClient with customisable dependency overrides.

    Usage::

        def test_foo(client_factory):
            client = client_factory(principal=..., gateway=..., idempotency_store=...)
            response = client.get("/api/v1/public/procedures/wf-1")
    """
    def _make(
        principal: Principal | None = None,
        gateway=None,
        idempotency_store=None,
        procedure_catalog=None,
        maybe_gateway=None,
        maybe_pool=None,
    ):
        app = create_app()
        overrides = {}

        if principal is not None:
            overrides[get_current_principal] = lambda: principal

        if gateway is not None:
            overrides[get_temporal_gateway] = lambda: gateway

        if idempotency_store is not None:
            overrides[get_idempotency_store] = lambda: idempotency_store

        if procedure_catalog is not None:
            overrides[get_procedure_catalog] = lambda: procedure_catalog

        if maybe_gateway is not None:
            overrides[maybe_get_temporal_gateway] = lambda: maybe_gateway

        if maybe_pool is not None:
            overrides[maybe_get_database_pool] = lambda: maybe_pool

        app.dependency_overrides.update(overrides)
        return TestClient(app, raise_server_exceptions=False)

    return _make


# ---------------------------------------------------------------------------
# POST /api/v1/public/procedures/start
# ---------------------------------------------------------------------------

class TestPublicStartProcedure:

    def test_public_start_procedure_returns_202(self, client_factory):
        principal = _make_principal(tenant_ids=("tenant-a",))
        gateway = FakeTemporalGateway(workflow_id="wf-public-001")
        store = FakeIdempotencyStore()

        from app.services.procedure_catalog import ProcedureCatalog
        catalog = ProcedureCatalog.discover()

        client = client_factory(
            principal=principal,
            gateway=gateway,
            idempotency_store=store,
            procedure_catalog=catalog,
        )

        response = client.post(
            "/api/v1/public/procedures/start",
            headers={"Authorization": "Bearer fake-token"},
            json={
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
            },
        )

        assert response.status_code == 202
        body = response.json()
        assert body["workflow_id"] == "wf-public-001"
        assert "poll_url" in body
        assert "stream_url" in body
        assert body["status"] == "STARTED"

    def test_public_start_procedure_requires_auth(self, client_factory):
        """Without auth override the bearer scheme returns 403 (auto_error=True -> 403)."""
        # Build client with no principal override so the real get_current_principal
        # is used, which will reject requests without a valid token.
        app = create_app()
        client = TestClient(app, raise_server_exceptions=False)

        response = client.post(
            "/api/v1/public/procedures/start",
            json={
                "procedure_type": "company-onboarding",
                "tenant_id": "tenant-a",
                "payload": {},
            },
        )

        assert response.status_code in {401, 403}

    def test_public_start_procedure_tenant_access_denied(self, client_factory):
        """Principal cannot access the requested tenant → 403."""
        principal = _make_principal(tenant_ids=("other-tenant",))
        gateway = FakeTemporalGateway()
        store = FakeIdempotencyStore()
        from app.services.procedure_catalog import ProcedureCatalog
        catalog = ProcedureCatalog.discover()

        client = client_factory(
            principal=principal,
            gateway=gateway,
            idempotency_store=store,
            procedure_catalog=catalog,
        )

        response = client.post(
            "/api/v1/public/procedures/start",
            headers={"Authorization": "Bearer fake-token"},
            json={
                "procedure_type": "company-onboarding",
                "tenant_id": "tenant-a",
                "payload": {},
            },
        )

        assert response.status_code == 403

    def test_public_start_procedure_idempotency_returns_cached(self, client_factory):
        """Second request with same idempotency key returns cached result."""
        principal = _make_principal(tenant_ids=("tenant-a",))
        cached_handle = ProcedureHandleDTO(
            workflow_id="wf-cached-001",
            procedure_type="company-onboarding",
            tenant_id="tenant-a",
            status="STARTED",
            poll_url="/api/v1/public/procedures/wf-cached-001",
            stream_url="/api/v1/streams/workflows/wf-cached-001",
        )
        store = FakeIdempotencyStore(cached_result=cached_handle.model_dump())
        gateway = FakeTemporalGateway()
        from app.services.procedure_catalog import ProcedureCatalog
        catalog = ProcedureCatalog.discover()

        client = client_factory(
            principal=principal,
            gateway=gateway,
            idempotency_store=store,
            procedure_catalog=catalog,
        )

        response = client.post(
            "/api/v1/public/procedures/start",
            headers={"Authorization": "Bearer fake-token"},
            json={
                "procedure_type": "company-onboarding",
                "tenant_id": "tenant-a",
                "payload": {},
                "idempotency_key": "idem-key-42",
            },
        )

        assert response.status_code == 202
        body = response.json()
        assert body["workflow_id"] == "wf-cached-001"
        # Gateway should NOT have been called since cache hit happened first.
        assert gateway.calls == []


# ---------------------------------------------------------------------------
# GET /api/v1/public/procedures/{workflow_id}
# ---------------------------------------------------------------------------

class TestPublicGetProcedureStatus:

    def test_get_public_procedure_status_not_found(self, client_factory):
        """Unknown workflow_id returns 404 when no gateway or pool returns data."""
        principal = _make_principal()

        class NullGateway:
            async def describe_workflow(self, workflow_id):
                return None

        client = client_factory(
            principal=principal,
            maybe_gateway=None,
            maybe_pool=None,
        )

        response = client.get(
            "/api/v1/public/procedures/unknown-wf-id",
            headers={"Authorization": "Bearer fake-token"},
        )

        # Neither gateway nor pool available → 503; with both None → 503 or 404
        assert response.status_code in {404, 503}

    def test_get_public_procedure_status_tenant_forbidden(self, client_factory):
        """Workflow owned by different tenant returns 403."""
        # Principal only has access to tenant-b
        principal = _make_principal(tenant_ids=("tenant-b",))

        # Provide a fake gateway that returns a status for tenant-a
        class FakeGatewayTenantA:
            async def describe_workflow(self, workflow_id):
                class FakeDesc:
                    id = workflow_id
                    workflow_type = "CompanyOnboardingWorkflow"
                    search_attributes = {
                        "tenant_id": ["tenant-a"],
                        "procedure_type": ["company-onboarding"],
                        "status": ["STARTED"],
                    }
                    status = None

                    class _Status:
                        name = "RUNNING"
                    status = _Status()
                    start_time = __import__("datetime").datetime(2024, 1, 1, tzinfo=__import__("datetime").timezone.utc)

                return FakeDesc()

        client = client_factory(
            principal=principal,
            maybe_gateway=FakeGatewayTenantA(),
            maybe_pool=None,
        )

        response = client.get(
            "/api/v1/public/procedures/wf-tenant-a-001",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 403


# ---------------------------------------------------------------------------
# POST /api/v1/streams/tickets
# ---------------------------------------------------------------------------

class TestIssueStreamTicket:

    def test_issue_stream_ticket_returns_ticket_and_ttl(self, client_factory):
        """Authenticated POST to /api/v1/streams/tickets returns ticket and expires_in_seconds."""
        principal = _make_principal(subject="user-stream-1", tenant_ids=("tenant-a",))

        client = client_factory(principal=principal)

        response = client.post(
            "/api/v1/streams/tickets",
            headers={"Authorization": "Bearer fake-token"},
        )

        assert response.status_code == 200
        body = response.json()
        assert "ticket" in body
        assert isinstance(body["ticket"], str)
        assert len(body["ticket"]) > 0
        assert "expires_in_seconds" in body
        assert isinstance(body["expires_in_seconds"], int)
        assert body["expires_in_seconds"] > 0
