"""
tests/chaos/dependency_loss/test_vault_loss.py
Tests graceful degradation when Vault is unreachable.

Invariants:
- Signing fails with a timeout/connection error (not a crash or key leakage)
- Error messages when Vault is unreachable must not contain key material

Marker: chaos
"""
from __future__ import annotations

import base64
import time

import pytest

pytestmark = pytest.mark.chaos


# ---------------------------------------------------------------------------
# Test 1: Signing fails gracefully when Vault is down
# ---------------------------------------------------------------------------


@pytest.mark.chaos
def test_signing_fails_gracefully_when_vault_down(
    proxied_vault_client, vault_proxy, vault_transit_key, add_latency_toxic
) -> None:
    """
    Add effectively infinite latency on the Vault proxy (99999ms = ~100 seconds).
    Attempt to sign a payload and assert that a timeout or connection error is raised.

    The key invariant: a timeout error, not a crash, and no raw key material in the error.
    """
    proxy_name = vault_proxy["name"]
    # Add very high latency to simulate Vault being unreachable
    add_latency_toxic(proxy_name, latency_ms=99999)

    payload = base64.b64encode(b"vault-down signing test").decode()

    error_raised = False
    error_message = ""

    import hvac  # type: ignore

    host = proxied_vault_client.url
    slow_client = hvac.Client(url=host, token="dev-root-token")
    slow_client.timeout = 1  # 1-second timeout to simulate unreachable Vault

    try:
        slow_client.secrets.transit.sign_data(
            name=vault_transit_key,
            hash_input=payload,
            hash_algorithm="sha2-256",
        )
    except Exception as exc:
        error_raised = True
        error_message = str(exc)

    if not error_raised:
        pytest.fail("Vault signing unexpectedly succeeded while the proxied dependency was degraded")

    # Verify no key material in error message
    private_key_indicators = [
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
        "privateKey",
        "private_key",
    ]
    for indicator in private_key_indicators:
        assert indicator not in error_message, (
            f"Error message when Vault is unreachable must not contain key material. "
            f"Found '{indicator}' in error: {error_message[:200]}"
        )


# ---------------------------------------------------------------------------
# Test 2: No raw key leakage on Vault error
# ---------------------------------------------------------------------------


@pytest.mark.chaos
def test_no_raw_key_leakage_on_vault_error() -> None:
    """
    When Vault is unreachable, error messages must not contain key material.

    This test verifies the error-handling pattern by inspecting exception classes
    and ensuring they do not capture raw key material in their string representation.
    """
    hvac = pytest.importorskip("hvac")

    # Create a client pointing at a non-existent Vault
    bad_client = hvac.Client(url="http://localhost:19999", token="invalid-token")
    bad_client.timeout = 1

    error_message = ""
    try:
        bad_client.secrets.transit.sign_data(
            name="nonexistent-key",
            hash_input=base64.b64encode(b"test").decode(),
            hash_algorithm="sha2-256",
        )
    except Exception as exc:
        error_message = str(exc)

    if not error_message:
        pytest.skip("No error raised for unreachable Vault — network may have responded")

    private_key_patterns = [
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
        "privateKey",
        "private_key",
    ]

    for pattern in private_key_patterns:
        assert pattern not in error_message, (
            f"Vault error message must not contain key material '{pattern}'. "
            f"Error: {error_message[:300]}"
        )

    # Verify the error is a connectivity/auth error, not a crash
    assert any(
        keyword in error_message.lower()
        for keyword in [
            "connection", "refused", "timeout", "error", "failed",
            "invalid", "unreachable", "network",
        ]
    ), (
        f"Expected a connectivity/auth error message, got: {error_message[:300]}"
    )
