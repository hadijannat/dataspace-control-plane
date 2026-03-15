#!/usr/bin/env python3
"""
tests/scripts/seed_test_realms.py
Seed a Keycloak test realm with realm, confidential client, and operator user.

Usage:
    python tests/scripts/seed_test_realms.py \
        --keycloak-url http://localhost:8080 \
        --admin-password admin \
        --realm dataspace-test

Exits 0 on success, 1 on failure. Prints client_secret at the end.
"""
from __future__ import annotations

import argparse
import secrets
import sys


def _get_admin_token(base_url: str, admin_password: str) -> str:
    """Obtain master realm admin access token."""
    import urllib.parse
    import urllib.request

    data = urllib.parse.urlencode({
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": "admin",
        "password": admin_password,
    }).encode()

    req = urllib.request.Request(
        f"{base_url}/realms/master/protocol/openid-connect/token",
        data=data,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        import json
        return json.loads(resp.read())["access_token"]


def _api_post(url: str, token: str, payload: dict) -> dict:
    import json
    import urllib.request

    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = resp.read()
        if body:
            return json.loads(body)
        return {}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--keycloak-url", required=True, help="Keycloak base URL")
    parser.add_argument("--admin-password", default="admin", help="Admin password (default: admin)")
    parser.add_argument("--realm", default="dataspace-test", help="Realm name to create")
    args = parser.parse_args(argv)

    base_url = args.keycloak_url.rstrip("/")
    realm = args.realm

    try:
        print(f"Obtaining admin token from {base_url} ...")
        token = _get_admin_token(base_url, args.admin_password)
        print("  OK")

        # 1. Create realm
        print(f"Creating realm '{realm}' ...")
        _api_post(
            f"{base_url}/admin/realms",
            token,
            {"realm": realm, "enabled": True, "displayName": f"{realm} (test)"},
        )
        print("  OK")

        # 2. Create confidential client
        print("Creating client 'control-api-test' ...")
        client_secret = secrets.token_urlsafe(32)
        _api_post(
            f"{base_url}/admin/realms/{realm}/clients",
            token,
            {
                "clientId": "control-api-test",
                "enabled": True,
                "publicClient": False,
                "serviceAccountsEnabled": True,
                "standardFlowEnabled": False,
                "directAccessGrantsEnabled": False,
                "secret": client_secret,
                "protocol": "openid-connect",
            },
        )
        print("  OK")

        # 3. Create operator user
        print("Creating user 'operator@test.local' ...")
        _api_post(
            f"{base_url}/admin/realms/{realm}/users",
            token,
            {
                "username": "operator@test.local",
                "email": "operator@test.local",
                "enabled": True,
                "credentials": [
                    {"type": "password", "value": "TestPassword123!", "temporary": False}
                ],
            },
        )
        print("  OK")

        # 4. Create operator realm role
        print("Creating realm role 'operator' ...")
        _api_post(
            f"{base_url}/admin/realms/{realm}/roles",
            token,
            {"name": "operator", "description": "Human operator role"},
        )
        print("  OK")

        print(f"\nRealm '{realm}' seeded successfully.")
        print(f"client_id:     control-api-test")
        print(f"client_secret: {client_secret}")
        return 0

    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
