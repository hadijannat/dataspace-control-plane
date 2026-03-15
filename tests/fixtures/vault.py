"""
HashiCorp Vault fixtures: transit key setup, PKI role creation, policy fixtures.
Depends on vault_container from fixtures/containers.py.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Vault client
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def vault_client(vault_container):
    """
    Session-scoped authenticated hvac.Client pointed at vault_container.

    Uses the dev root token 'dev-root-token'.
    Skipped if hvac is not installed.
    """
    hvac = pytest.importorskip("hvac", reason="hvac required for vault_client")
    host = vault_container.get_container_host_ip()
    port = vault_container.get_exposed_port(8200)
    url = f"http://{host}:{port}"
    client = hvac.Client(url=url, token="dev-root-token")
    assert client.is_authenticated(), "Vault client authentication failed"
    return client


# ---------------------------------------------------------------------------
# Transit key
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def vault_transit_key(vault_client) -> str:
    """
    Session-scoped fixture that enables Transit secrets engine and creates
    an ECDSA-P256 signing key named 'dataspace-signing'.

    Yields the key name.
    """
    import hvac.exceptions  # type: ignore

    # Enable transit engine (ignore if already mounted)
    try:
        vault_client.sys.enable_secrets_engine(
            backend_type="transit",
            path="transit",
        )
    except hvac.exceptions.InvalidRequest:
        pass  # Already mounted

    key_name = "dataspace-signing"
    try:
        vault_client.secrets.transit.create_key(
            name=key_name,
            key_type="ecdsa-p256",
            exportable=False,
            allow_plaintext_backup=False,
        )
    except hvac.exceptions.InvalidRequest:
        pass  # Key already exists

    yield key_name

    # Teardown: delete key (requires deletion_allowed=true)
    try:
        vault_client.secrets.transit.update_key_configuration(
            name=key_name,
            deletion_allowed=True,
        )
        vault_client.secrets.transit.delete_key(name=key_name)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# PKI role
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def vault_pki_role(vault_client) -> str:
    """
    Session-scoped fixture that enables PKI secrets engine, generates an
    internal root CA, and creates role 'dataspace-service' with 24h TTL.

    Yields the role name.
    """
    import hvac.exceptions  # type: ignore

    # Enable PKI engine
    try:
        vault_client.sys.enable_secrets_engine(
            backend_type="pki",
            path="pki",
        )
    except hvac.exceptions.InvalidRequest:
        pass

    # Tune the mount TTL to 10 years
    vault_client.sys.tune_mount_configuration(
        path="pki",
        max_lease_ttl="87600h",
    )

    # Generate internal root cert
    try:
        vault_client.secrets.pki.generate_root(
            type="internal",
            common_name="Dataspace Test CA",
            ttl="87600h",
        )
    except Exception:
        pass

    # Create role
    role_name = "dataspace-service"
    vault_client.secrets.pki.create_or_update_role(
        name=role_name,
        extra_params={
            "ttl": "24h",
            "max_ttl": "24h",
            "allow_any_name": True,
            "generate_lease": True,
        },
    )
    yield role_name
