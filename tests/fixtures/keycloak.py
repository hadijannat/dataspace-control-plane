"""
Keycloak Admin REST fixtures: realm seeding, client creation, and user seeding.
Depends on keycloak_container from fixtures/containers.py.
"""
from __future__ import annotations

import os
from typing import Any

import pytest


REALM_NAME = "dataspace-test"
SERVICE_CLIENT_ID = "control-api-test"
BROWSER_CLIENT_ID = "web-console-test"
OPERATOR_ROLE_NAME = "operator"
OPERATOR_USERNAME = "operator@test.local"
OPERATOR_PASSWORD = "TestPassword123!"


def _requests():
    return pytest.importorskip("requests", reason="requests required for keycloak fixtures")


def _auth_headers(base_url: str) -> dict[str, str]:
    token = _get_admin_token(base_url)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def _get_admin_token(base_url: str) -> str:
    """Obtain a master realm admin token."""
    requests = _requests()
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


def _get_client(base_url: str, realm: str, client_id: str) -> dict[str, Any] | None:
    requests = _requests()
    resp = requests.get(
        f"{base_url}/admin/realms/{realm}/clients",
        headers=_auth_headers(base_url),
        params={"clientId": client_id},
        timeout=10,
    )
    resp.raise_for_status()
    clients = resp.json()
    return clients[0] if clients else None


def _upsert_client(base_url: str, realm: str, payload: dict[str, Any]) -> dict[str, Any]:
    requests = _requests()
    headers = _auth_headers(base_url)
    existing = _get_client(base_url, realm, payload["clientId"])
    if existing is None:
        resp = requests.post(
            f"{base_url}/admin/realms/{realm}/clients",
            json=payload,
            headers=headers,
            timeout=10,
        )
        if resp.status_code not in {201, 409}:
            resp.raise_for_status()
        existing = _get_client(base_url, realm, payload["clientId"])
    else:
        resp = requests.put(
            f"{base_url}/admin/realms/{realm}/clients/{existing['id']}",
            json={**existing, **payload},
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        existing = _get_client(base_url, realm, payload["clientId"])

    assert existing is not None, f"Keycloak client {payload['clientId']} was not created"
    return existing


def _get_client_secret(base_url: str, realm: str, internal_client_id: str) -> str:
    requests = _requests()
    resp = requests.get(
        f"{base_url}/admin/realms/{realm}/clients/{internal_client_id}/client-secret",
        headers=_auth_headers(base_url),
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["value"]


def _get_user(base_url: str, realm: str, username: str) -> dict[str, Any] | None:
    requests = _requests()
    resp = requests.get(
        f"{base_url}/admin/realms/{realm}/users",
        headers=_auth_headers(base_url),
        params={"username": username, "exact": "true"},
        timeout=10,
    )
    resp.raise_for_status()
    users = resp.json()
    return users[0] if users else None


def _ensure_operator_role(base_url: str, realm: str) -> dict[str, Any]:
    requests = _requests()
    headers = _auth_headers(base_url)
    resp = requests.post(
        f"{base_url}/admin/realms/{realm}/roles",
        json={"name": OPERATOR_ROLE_NAME, "description": "Operator role for human users"},
        headers=headers,
        timeout=10,
    )
    if resp.status_code not in {201, 409}:
        resp.raise_for_status()

    role_resp = requests.get(
        f"{base_url}/admin/realms/{realm}/roles/{OPERATOR_ROLE_NAME}",
        headers=headers,
        timeout=10,
    )
    role_resp.raise_for_status()
    return role_resp.json()


def _assign_realm_role(base_url: str, realm: str, user_id: str, role: dict[str, Any]) -> None:
    requests = _requests()
    headers = _auth_headers(base_url)
    current = requests.get(
        f"{base_url}/admin/realms/{realm}/users/{user_id}/role-mappings/realm",
        headers=headers,
        timeout=10,
    )
    current.raise_for_status()
    if any(entry.get("name") == role["name"] for entry in current.json()):
        return

    resp = requests.post(
        f"{base_url}/admin/realms/{realm}/users/{user_id}/role-mappings/realm",
        json=[role],
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()


# ---------------------------------------------------------------------------
# Admin URL
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def keycloak_admin_url(keycloak_container) -> str:
    """Session-scoped Keycloak Admin REST base URL."""
    host = keycloak_container.get_container_host_ip()
    port = keycloak_container.get_exposed_port(8080)
    return f"http://{host}:{port}"


@pytest.fixture(scope="session")
def keycloak_admin_token(keycloak_admin_url: str) -> str:
    """Fresh admin token for tests that need to inspect seeded Keycloak state."""
    return _get_admin_token(keycloak_admin_url)


# ---------------------------------------------------------------------------
# Realm
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def keycloak_realm(keycloak_admin_url: str) -> str:
    """
    Session-scoped fixture that creates realm 'dataspace-test' via Admin REST.

    Yields the realm name and deletes it on teardown.
    """
    requests = _requests()
    headers = _auth_headers(keycloak_admin_url)
    resp = requests.post(
        f"{keycloak_admin_url}/admin/realms",
        json={
            "realm": REALM_NAME,
            "enabled": True,
            "displayName": "Dataspace Test Realm",
        },
        headers=headers,
        timeout=15,
    )
    if resp.status_code not in {201, 409}:
        resp.raise_for_status()

    yield REALM_NAME

    try:
        requests.delete(
            f"{keycloak_admin_url}/admin/realms/{REALM_NAME}",
            headers=_auth_headers(keycloak_admin_url),
            timeout=10,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def keycloak_client(keycloak_admin_url: str, keycloak_realm: str) -> dict[str, str]:
    """
    Session-scoped confidential service client for machine-to-machine tests.

    Returns the client id, internal Keycloak id, and current client secret.
    """
    client = _upsert_client(
        keycloak_admin_url,
        keycloak_realm,
        {
            "clientId": SERVICE_CLIENT_ID,
            "enabled": True,
            "publicClient": False,
            "serviceAccountsEnabled": True,
            "standardFlowEnabled": False,
            "directAccessGrantsEnabled": False,
            "protocol": "openid-connect",
        },
    )
    secret = _get_client_secret(keycloak_admin_url, keycloak_realm, client["id"])
    return {
        "client_id": SERVICE_CLIENT_ID,
        "internal_id": client["id"],
        "client_secret": secret,
    }


@pytest.fixture(scope="session")
def keycloak_browser_client(keycloak_admin_url: str, keycloak_realm: str) -> dict[str, str]:
    """
    Session-scoped public browser client for Authorization Code + PKCE flows.
    """
    web_console_url = os.environ.get("WEB_CONSOLE_URL", "http://localhost:3000").rstrip("/")
    redirect_uris = [
        f"{web_console_url}/*",
        "http://localhost:3000/*",
        "http://localhost:5173/*",
    ]
    client = _upsert_client(
        keycloak_admin_url,
        keycloak_realm,
        {
            "clientId": BROWSER_CLIENT_ID,
            "enabled": True,
            "publicClient": True,
            "serviceAccountsEnabled": False,
            "standardFlowEnabled": True,
            "directAccessGrantsEnabled": False,
            "redirectUris": redirect_uris,
            "webOrigins": ["+"],
            "protocol": "openid-connect",
        },
    )
    return {
        "client_id": BROWSER_CLIENT_ID,
        "internal_id": client["id"],
        "redirect_uri": f"{web_console_url}/dashboard",
    }


# ---------------------------------------------------------------------------
# Operator user
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def keycloak_operator_user(keycloak_admin_url: str, keycloak_realm: str) -> dict[str, str]:
    """
    Session-scoped operator user with the 'operator' realm role assigned.
    """
    requests = _requests()
    headers = _auth_headers(keycloak_admin_url)
    role = _ensure_operator_role(keycloak_admin_url, keycloak_realm)
    existing = _get_user(keycloak_admin_url, keycloak_realm, OPERATOR_USERNAME)

    if existing is None:
        resp = requests.post(
            f"{keycloak_admin_url}/admin/realms/{keycloak_realm}/users",
            json={
                "username": OPERATOR_USERNAME,
                "email": OPERATOR_USERNAME,
                "enabled": True,
            },
            headers=headers,
            timeout=10,
        )
        if resp.status_code not in {201, 409}:
            resp.raise_for_status()
        existing = _get_user(keycloak_admin_url, keycloak_realm, OPERATOR_USERNAME)

    assert existing is not None, "operator user was not created in Keycloak"

    password_resp = requests.put(
        f"{keycloak_admin_url}/admin/realms/{keycloak_realm}/users/{existing['id']}/reset-password",
        json={"type": "password", "value": OPERATOR_PASSWORD, "temporary": False},
        headers=headers,
        timeout=10,
    )
    password_resp.raise_for_status()

    _assign_realm_role(keycloak_admin_url, keycloak_realm, existing["id"], role)

    return {
        "id": existing["id"],
        "username": OPERATOR_USERNAME,
        "password": OPERATOR_PASSWORD,
        "role": OPERATOR_ROLE_NAME,
    }
