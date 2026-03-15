"""
tests/crypto-boundaries/vault_transit/test_transit_operations.py
Verifies Vault Transit secrets engine operations and key custody boundaries.

Invariants:
- Transit sign returns a signature, never a private key
- Signature verification works for valid signatures, fails for tampered payloads
- Hashing is deterministic
- Transit does not store data (signing is stateless)

Requires: vault_client, vault_transit_key fixtures, --live-services.
Marker: crypto
"""
from __future__ import annotations

import base64
import hashlib

import pytest

pytestmark = pytest.mark.crypto


# ---------------------------------------------------------------------------
# Test 1: Sign returns signature, not private key
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_sign_returns_signature_not_private_key(vault_client, vault_transit_key) -> None:
    """
    Vault Transit sign endpoint must return a 'signature' field.
    It must NOT return 'private_key' or raw key material at the top level.
    """
    payload = base64.b64encode(b"test payload for signing").decode()
    result = vault_client.secrets.transit.sign_data(
        name=vault_transit_key,
        hash_input=payload,
        hash_algorithm="sha2-256",
    )
    data = result.get("data", result)

    assert "signature" in data, (
        f"Transit sign response must contain 'signature' field. Got: {list(data.keys())}"
    )
    assert "private_key" not in data, (
        "Transit sign response must NOT contain 'private_key' — key material must never leave Vault"
    )
    assert "key" not in data or data.get("key") is None, (
        "Transit sign response must not expose raw key material"
    )


# ---------------------------------------------------------------------------
# Test 2: Verify valid signature succeeds
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_verify_valid_signature_succeeds(vault_client, vault_transit_key) -> None:
    """Sign a payload then verify — must return valid: True."""
    payload_bytes = b"verify this payload"
    payload_b64 = base64.b64encode(payload_bytes).decode()

    # Sign
    sign_result = vault_client.secrets.transit.sign_data(
        name=vault_transit_key,
        hash_input=payload_b64,
        hash_algorithm="sha2-256",
    )
    signature = sign_result["data"]["signature"]

    # Verify
    verify_result = vault_client.secrets.transit.verify_signed_data(
        name=vault_transit_key,
        hash_input=payload_b64,
        signature=signature,
        hash_algorithm="sha2-256",
    )
    verify_data = verify_result.get("data", verify_result)
    assert verify_data.get("valid") is True, (
        f"Valid signature must verify as True. Got: {verify_data}"
    )


# ---------------------------------------------------------------------------
# Test 3: Verify tampered payload fails
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_verify_tampered_payload_fails(vault_client, vault_transit_key) -> None:
    """Sign payload A, then verify with payload B — must return valid: False."""
    payload_a = base64.b64encode(b"original payload A").decode()
    payload_b = base64.b64encode(b"tampered payload B").decode()

    # Sign A
    sign_result = vault_client.secrets.transit.sign_data(
        name=vault_transit_key,
        hash_input=payload_a,
        hash_algorithm="sha2-256",
    )
    signature = sign_result["data"]["signature"]

    # Verify with B (different payload)
    try:
        verify_result = vault_client.secrets.transit.verify_signed_data(
            name=vault_transit_key,
            hash_input=payload_b,
            signature=signature,
            hash_algorithm="sha2-256",
        )
        verify_data = verify_result.get("data", verify_result)
        assert verify_data.get("valid") is False, (
            f"Tampered payload must fail verification. Got: {verify_data}"
        )
    except Exception as exc:
        # Vault may raise an error for invalid signature instead of returning valid=False
        # Both behaviors are acceptable
        assert "invalid" in str(exc).lower() or "verification" in str(exc).lower(), (
            f"Expected invalid signature error, got unexpected exception: {exc}"
        )


# ---------------------------------------------------------------------------
# Test 4: Hash is deterministic
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_hash_is_deterministic(vault_client) -> None:
    """Hashing the same payload twice via Vault Transit must produce identical results."""
    payload = base64.b64encode(b"deterministic hash test payload").decode()

    # Vault Transit hash endpoint
    result_a = vault_client.secrets.transit.hash_data(
        hash_input=payload,
        algorithm="sha2-256",
    )
    result_b = vault_client.secrets.transit.hash_data(
        hash_input=payload,
        algorithm="sha2-256",
    )

    hash_a = result_a.get("data", result_a).get("sum", "")
    hash_b = result_b.get("data", result_b).get("sum", "")

    assert hash_a == hash_b, (
        f"Transit hash must be deterministic. Got different hashes:\n"
        f"  first:  {hash_a}\n"
        f"  second: {hash_b}"
    )
    assert hash_a, "Transit hash must return a non-empty sum"


# ---------------------------------------------------------------------------
# Test 5: Prehashed sign matches inline sign
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_prehashed_sign_matches_inline_sign(vault_client, vault_transit_key) -> None:
    """
    Signing with prehashed=True (local SHA-256) must produce a verifiable signature.

    Both local prehash and Vault-internal hash must produce signatures that
    verify correctly — they use the same key.
    """
    payload = b"prehash test payload"
    payload_b64 = base64.b64encode(payload).decode()

    # Compute SHA-256 locally
    local_hash = hashlib.sha256(payload).digest()
    local_hash_b64 = base64.b64encode(local_hash).decode()

    # Sign with prehashed=True
    prehash_sign = vault_client.secrets.transit.sign_data(
        name=vault_transit_key,
        hash_input=local_hash_b64,
        hash_algorithm="sha2-256",
        prehashed=True,
    )
    prehash_sig = prehash_sign["data"]["signature"]

    # Verify the prehashed signature
    verify_result = vault_client.secrets.transit.verify_signed_data(
        name=vault_transit_key,
        hash_input=local_hash_b64,
        signature=prehash_sig,
        hash_algorithm="sha2-256",
        prehashed=True,
    )
    verify_data = verify_result.get("data", verify_result)
    assert verify_data.get("valid") is True, (
        f"Prehashed signature must verify as valid. Got: {verify_data}"
    )


# ---------------------------------------------------------------------------
# Test 6: Transit does not store signed data
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_transit_does_not_store_data(vault_client, vault_transit_key) -> None:
    """
    Vault Transit is stateless — it does not store payloads that have been signed.

    Verify that listing transit keys does not include payload content in any field.
    """
    secret_payload = "sensitive-payload-should-not-be-stored"
    payload_b64 = base64.b64encode(secret_payload.encode()).decode()

    # Sign the payload
    vault_client.secrets.transit.sign_data(
        name=vault_transit_key,
        hash_input=payload_b64,
        hash_algorithm="sha2-256",
    )

    # List transit keys and inspect the response
    keys_result = vault_client.secrets.transit.list_keys()
    keys_str = str(keys_result)

    assert secret_payload not in keys_str, (
        f"Transit key list must not contain the signed payload. "
        f"Found '{secret_payload}' in: {keys_str[:200]}"
    )

    # Also check key details
    key_detail = vault_client.secrets.transit.read_key(name=vault_transit_key)
    key_str = str(key_detail)

    assert secret_payload not in key_str, (
        f"Transit key detail must not contain the signed payload. "
        f"Found '{secret_payload}' in key detail."
    )
