"""
Verifies auth grant-type boundaries between human operators and machine services.
"""
from __future__ import annotations

import base64
import json

import pytest

pytestmark = pytest.mark.crypto

requests = pytest.importorskip("requests")


def _decode_jwt_claims(token: str) -> dict:
    """Decode JWT claims from a token without signature verification."""
    parts = token.split(".")
    if len(parts) < 2:
        return {}
    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    decoded = base64.b64decode(payload, altchars=b"-_")
    return json.loads(decoded)


def test_browser_client_uses_authorization_code_flow(
    keycloak_admin_url, keycloak_admin_token, keycloak_realm, keycloak_browser_client
) -> None:
    """
    The browser-facing client must use Authorization Code + PKCE, not service accounts.
    """
    resp = requests.get(
        f"{keycloak_admin_url}/admin/realms/{keycloak_realm}/clients/{keycloak_browser_client['internal_id']}",
        headers={"Authorization": f"Bearer {keycloak_admin_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    client_config = resp.json()

    assert client_config["standardFlowEnabled"] is True
    assert client_config["publicClient"] is True
    assert client_config["serviceAccountsEnabled"] is False
    assert client_config["directAccessGrantsEnabled"] is False

def test_service_client_uses_client_credentials(
    keycloak_client, keycloak_admin_url, keycloak_realm
) -> None:
    """
    The confidential service client must support client_credentials grant.
    """
    resp = requests.post(
        f"{keycloak_admin_url}/realms/{keycloak_realm}/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": keycloak_client["client_id"],
            "client_secret": keycloak_client["client_secret"],
        },
        timeout=10,
    )
    assert resp.status_code == 200, (
        f"Service client must support client_credentials grant. Got {resp.status_code}: {resp.text}"
    )
    assert "access_token" in resp.json()


def test_operator_user_has_operator_role_via_admin_mapping(
    keycloak_admin_url, keycloak_admin_token, keycloak_realm, keycloak_operator_user
) -> None:
    """
    The operator user must actually be assigned the operator realm role.
    """
    headers = {"Authorization": f"Bearer {keycloak_admin_token}"}
    resp = requests.get(
        f"{keycloak_admin_url}/admin/realms/{keycloak_realm}/users/{keycloak_operator_user['id']}/role-mappings/realm",
        headers=headers,
        timeout=10,
    )
    resp.raise_for_status()
    roles = {entry["name"] for entry in resp.json()}
    assert keycloak_operator_user["role"] in roles


def test_machine_token_lacks_operator_role(
    keycloak_admin_url, keycloak_realm, keycloak_client
) -> None:
    """
    A machine token for the service client must not receive human operator privileges.
    """
    resp = requests.post(
        f"{keycloak_admin_url}/realms/{keycloak_realm}/protocol/openid-connect/token",
        data={
            "grant_type": "client_credentials",
            "client_id": keycloak_client["client_id"],
            "client_secret": keycloak_client["client_secret"],
        },
        timeout=10,
    )
    resp.raise_for_status()

    claims = _decode_jwt_claims(resp.json()["access_token"])
    realm_roles = claims.get("realm_access", {}).get("roles", [])
    assert "operator" not in realm_roles, (
        f"Machine tokens must not carry the operator role. Got roles: {realm_roles}"
    )
