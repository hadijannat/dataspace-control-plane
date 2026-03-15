"""
Unit tests for the runtime configuration endpoint.

Covers:
- GET /ui/runtime-config.json
"""
import pytest
from fastapi.testclient import TestClient

from app.main import create_app

pytestmark = pytest.mark.unit


@pytest.fixture()
def client() -> TestClient:
    """TestClient with no dependency overrides — runtime-config needs no auth."""
    app = create_app()
    return TestClient(app, raise_server_exceptions=True)


class TestRuntimeConfig:

    def test_runtime_config_returns_expected_fields(self, client):
        """Response must include all required SPA bootstrap fields."""
        response = client.get("/ui/runtime-config.json")

        assert response.status_code == 200
        body = response.json()

        assert "apiBaseUrl" in body, "apiBaseUrl must be present"
        assert "keycloakUrl" in body, "keycloakUrl must be present"
        assert "keycloakRealm" in body, "keycloakRealm must be present"
        assert "keycloakClientId" in body, "keycloakClientId must be present"
        # tenantBanner may be null/None but the key must exist in the schema
        assert "tenantBanner" in body, "tenantBanner field must be present in response"

    def test_runtime_config_no_auth_required(self, client):
        """Endpoint must be accessible without an Authorization header."""
        response = client.get("/ui/runtime-config.json")
        # Must not return 401 or 403
        assert response.status_code not in {401, 403}
        assert response.status_code == 200

    def test_runtime_config_values_are_strings(self, client):
        """All non-nullable fields must be non-empty strings."""
        response = client.get("/ui/runtime-config.json")
        body = response.json()

        assert isinstance(body["apiBaseUrl"], str) and body["apiBaseUrl"]
        assert isinstance(body["keycloakUrl"], str) and body["keycloakUrl"]
        assert isinstance(body["keycloakRealm"], str) and body["keycloakRealm"]
        assert isinstance(body["keycloakClientId"], str) and body["keycloakClientId"]
