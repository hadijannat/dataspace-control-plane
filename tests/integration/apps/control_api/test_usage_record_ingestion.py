"""
Repo-wide control-api integration checks.

These tests intentionally cover only real runtime surfaces exposed by the app.
They must never fall back to a fake FastAPI app or silently skip missing routes.
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_liveness_endpoint_uses_real_control_api(test_client) -> None:
    """The repo-wide integration spine must hit the real /health/live route."""
    response = test_client.get("/health/live")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_readiness_endpoint_reports_dependency_state(async_client) -> None:
    """The readiness probe must be import-safe and return the declared health shape."""
    response = await async_client.get("/health/ready")
    assert response.status_code in {200, 503}
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert "version" in body


def test_runtime_config_endpoint_returns_web_console_bootstrap(test_client) -> None:
    """The UI bootstrap endpoint must return the Keycloak and API config expected by web-console."""
    response = test_client.get("/ui/runtime-config.json")
    assert response.status_code == 200
    body = response.json()
    assert body["apiBaseUrl"]
    assert body["keycloakUrl"]
    assert body["keycloakRealm"]
    assert body["keycloakClientId"]
