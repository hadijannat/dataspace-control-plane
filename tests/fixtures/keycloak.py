"""
Keycloak Admin REST fixtures: realm seeding, client creation, user seeding.
Depends on keycloak_container from fixtures/containers.py.
"""
from __future__ import annotations

import secrets

import pytest


# ---------------------------------------------------------------------------
# Admin URL
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def keycloak_admin_url(keycloak_container) -> str:
    """Session-scoped Keycloak Admin REST base URL."""
    host = keycloak_container.get_container_host_ip()
    port = keycloak_container.get_exposed_port(8080)
    return f"http://{host}:{port}"


def _get_admin_token(base_url: str) -> str:
    """Obtain a master realm admin token."""
    requests = pytest.importorskip("requests")
    resp = requests.post(
        f"{base_url}/realms/master/protocol/openid-connect/token",
        data={
            "grant_type": "password",
            "client_id": "admin-cli",
            "username": "admin",
            "password": "admin",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


# ---------------------------------------------------------------------------
# Realm
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def keycloak_realm(keycloak_admin_url: str) -> str:
    """
    Session-scoped fixture that creates realm 'dataspace-test' via Admin REST.

    Yields realm name. Deletes realm on teardown.
    Skipped if requests is not installed.
    """
    requests = pytest.importorskip("requests")
    realm_name = "dataspace-test"
    token = _get_admin_token(keycloak_admin_url)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    resp = requests.post(
        f"{keycloak_admin_url}/admin/realms",
        json={
            "realm": realm_name,
            "enabled": True,
            "displayName": "Dataspace Test Realm",
        },
        headers=headers,
        timeout=15,
    )
    resp.raise_for_status()

    yield realm_name

    # Teardown
    try:
        teardown_token = _get_admin_token(keycloak_admin_url)
        teardown_headers = {"Authorization": f"Bearer {teardown_token}"}
        requests.delete(
            f"{keycloak_admin_url}/admin/realms/{realm_name}",
            headers=teardown_headers,
            timeout=10,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def keycloak_client(keycloak_admin_url: str, keycloak_realm: str) -> dict:
    """
    Session-scoped fixture that creates confidential client 'control-api-test'.

    Yields dict with keys: client_id, client_secret.
    """
    requests = pytest.importorskip("requests")
    token = _get_admin_token(keycloak_admin_url)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    client_secret = secrets.token_urlsafe(32)
    client_payload = {
        "clientId": "control-api-test",
        "enabled": True,
        "publicClient": False,
        "serviceAccountsEnabled": True,
        "standardFlowEnabled": False,
        "directAccessGrantsEnabled": False,
        "secret": client_secret,
        "protocol": "openid-connect",
    }

    resp = requests.post(
        f"{keycloak_admin_url}/admin/realms/{keycloak_realm}/clients",
        json=client_payload,
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()

    yield {"client_id": "control-api-test", "client_secret": client_secret}


# ---------------------------------------------------------------------------
# Operator user
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def keycloak_operator_user(keycloak_admin_url: str, keycloak_realm: str) -> dict:
    """
    Session-scoped fixture that creates user operator@test.local with role 'operator'.

    Yields dict with keys: username, password.
    """
    requests = pytest.importorskip("requests")
    token = _get_admin_token(keycloak_admin_url)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    password = "TestPassword123!"

    # Create user
    resp = requests.post(
        f"{keycloak_admin_url}/admin/realms/{keycloak_realm}/users",
        json={
            "username": "operator@test.local",
            "email": "operator@test.local",
            "enabled": True,
            "credentials": [
                {"type": "password", "value": password, "temporary": False}
            ],
        },
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()

    # Create realm role 'operator'
    requests.post(
        f"{keycloak_admin_url}/admin/realms/{keycloak_realm}/roles",
        json={"name": "operator", "description": "Operator role for human users"},
        headers=headers,
        timeout=10,
    )

    yield {"username": "operator@test.local", "password": password}
