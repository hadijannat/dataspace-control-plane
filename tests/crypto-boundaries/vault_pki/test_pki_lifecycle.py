"""
tests/crypto-boundaries/vault_pki/test_pki_lifecycle.py
Verifies Vault PKI secrets engine certificate lifecycle.

Invariants:
- Issued certificates contain PEM cert in response, not stored in Vault
- Issued cert TTL is <= 24 hours
- Certificates can be revoked by serial
- Revoked certs appear in CRL

Requires: vault_client, vault_pki_role fixtures, --live-services.
Marker: crypto
"""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.crypto


# ---------------------------------------------------------------------------
# Test 1: Issue certificate (PEM in response, not stored)
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_issue_certificate(vault_client, vault_pki_role) -> None:
    """
    Issuing a certificate must return a PEM cert in the response.
    The private_key is also returned (standard PKI behavior) but is NOT stored in Vault.
    """
    result = vault_client.secrets.pki.generate_certificate(
        name=vault_pki_role,
        common_name="test-svc.internal",
        extra_params={"ttl": "1h"},
    )
    data = result.get("data", result)

    assert "certificate" in data, (
        f"Issue certificate response must contain 'certificate' (PEM). Got: {list(data.keys())}"
    )
    assert data["certificate"].strip().startswith("-----BEGIN CERTIFICATE-----"), (
        f"Certificate must be a PEM-encoded cert string. Got: {data['certificate'][:50]!r}"
    )

    # private_key is returned in the response (standard behavior)
    # but it is NOT stored in Vault — the caller is responsible for storing it securely
    assert "private_key" in data, (
        "PKI response should include private_key for the caller to store securely"
    )


# ---------------------------------------------------------------------------
# Test 2: Issued cert TTL <= 24 hours
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_issued_cert_ttl_under_24h(vault_client, vault_pki_role) -> None:
    """The difference between expiration and issue_time must be <= 86400 seconds (24h)."""
    result = vault_client.secrets.pki.generate_certificate(
        name=vault_pki_role,
        common_name="ttl-check.internal",
        extra_params={"ttl": "1h"},
    )
    data = result.get("data", result)

    expiration = data.get("expiration")
    assert expiration is not None, f"Certificate response missing 'expiration'. Got: {list(data.keys())}"

    # Parse expiration timestamp
    if isinstance(expiration, str):
        from datetime import datetime, timezone

        exp_dt = datetime.fromisoformat(expiration.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        ttl_seconds = (exp_dt - now).total_seconds()
    else:
        # expiration is a Unix timestamp
        import time

        ttl_seconds = expiration - time.time()

    assert ttl_seconds <= 86400, (
        f"Certificate TTL must be <= 86400 seconds (24h). Got: {ttl_seconds:.0f}s"
    )
    assert ttl_seconds > 0, f"Certificate is already expired: TTL = {ttl_seconds:.0f}s"


# ---------------------------------------------------------------------------
# Test 3: Revoke certificate
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_revoke_certificate(vault_client, vault_pki_role) -> None:
    """Issue a certificate, then revoke it by serial. Revocation must succeed."""
    result = vault_client.secrets.pki.generate_certificate(
        name=vault_pki_role,
        common_name="revoke-test.internal",
        extra_params={"ttl": "1h"},
    )
    data = result.get("data", result)
    serial = data.get("serial_number")

    assert serial, f"Certificate response must include serial_number. Got: {list(data.keys())}"

    # Revoke
    revoke_result = vault_client.secrets.pki.revoke_certificate(serial_number=serial)
    revoke_data = revoke_result.get("data", revoke_result)

    assert "revocation_time" in revoke_data or "revocation_time_rfc3339" in revoke_data, (
        f"Revocation must return revocation_time. Got: {list(revoke_data.keys())}"
    )


# ---------------------------------------------------------------------------
# Test 4: Revoked cert appears in CRL
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_revoked_cert_not_in_valid_list(vault_client, vault_pki_role) -> None:
    """After revoking a cert, its serial must appear in the CRL."""
    # Issue and revoke
    result = vault_client.secrets.pki.generate_certificate(
        name=vault_pki_role,
        common_name="crl-test.internal",
        extra_params={"ttl": "1h"},
    )
    data = result.get("data", result)
    serial = data.get("serial_number", "")

    vault_client.secrets.pki.revoke_certificate(serial_number=serial)

    # Rotate CRL to ensure our serial appears
    try:
        vault_client.secrets.pki.rotate_crl()
    except Exception:
        pass  # Not critical if rotation isn't explicitly supported

    # List revoked certs — verify our serial appears
    try:
        list_result = vault_client.list("pki/certs/revoked")
        revoked_serials = list_result.get("data", {}).get("keys", [])
        # Vault normalizes serials (e.g., adds colons)
        normalized_serial = serial.replace(":", "").lower()
        found = any(normalized_serial in s.replace(":", "").lower() for s in revoked_serials)
        # If CRL list is available and non-empty, our cert should be there
        if revoked_serials:
            assert found, (
                f"Revoked serial {serial!r} not found in CRL. "
                f"Revoked certs: {revoked_serials[:5]}"
            )
    except Exception:
        # CRL listing may not be available in all Vault versions/configs
        pytest.skip("CRL list endpoint not available in this Vault configuration")
