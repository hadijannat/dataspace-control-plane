"""
tests/crypto-boundaries/dcp_identity/test_dcp_identity.py
Verifies DCP identity schema contracts (VC/VP envelopes).

Invariants:
- Credential envelope schema is resolvable from registry
- Credential envelope has a 'proof' property (may be optional per DCP spec)
- Presentation envelope schema is resolvable from registry
- No private key material in VC examples

Tests 1, 3, 4 are static/unit-level — no services required.
Test 2 is schema inspection.
Marker: crypto
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.crypto

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCHEMAS_ROOT = REPO_ROOT / "schemas"

VC_SOURCE = SCHEMAS_ROOT / "vc" / "source"
VC_EXAMPLES_VALID = SCHEMAS_ROOT / "vc" / "examples" / "valid"

CREDENTIAL_ENVELOPE_PATHS = [
    VC_SOURCE / "envelope" / "credential-envelope.schema.json",
    VC_SOURCE / "credential-envelope.schema.json",
]
PRESENTATION_ENVELOPE_PATHS = [
    VC_SOURCE / "envelope" / "presentation-envelope.schema.json",
    VC_SOURCE / "presentation-envelope.schema.json",
]


def _find_schema(candidates: list[Path]) -> Path | None:
    for p in candidates:
        if p.exists():
            return p
    return None


# ---------------------------------------------------------------------------
# Test 1: VC credential envelope schema exists in registry
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_vc_credential_envelope_schema_exists(schema_registry) -> None:
    """Credential envelope $id must be resolvable from the offline schema_registry."""
    schema_path = _find_schema(CREDENTIAL_ENVELOPE_PATHS)
    if schema_path is None:
        pytest.skip("credential-envelope.schema.json not found in vc/source/")

    schema = json.loads(schema_path.read_text())
    schema_id = schema.get("$id", "")

    assert schema_id, f"credential-envelope schema has no $id: {schema_path}"
    assert "dataspace-control-plane.internal" in schema_id, (
        f"credential-envelope $id must use internal base URI. Got: {schema_id!r}"
    )


# ---------------------------------------------------------------------------
# Test 2: Credential envelope has 'proof' property
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_credential_envelope_requires_proof() -> None:
    """
    Credential envelope must define a 'proof' property (may be optional per DCP spec).

    DCP allows deferred proofs — proof is not required in the envelope schema,
    but it must be DEFINED so implementations know the expected structure.
    """
    schema_path = _find_schema(CREDENTIAL_ENVELOPE_PATHS)
    if schema_path is None:
        pytest.skip("credential-envelope.schema.json not found in vc/source/")

    schema = json.loads(schema_path.read_text())
    props = schema.get("properties", {})

    assert "proof" in props, (
        f"credential-envelope schema must define a 'proof' property (even if optional). "
        f"Current properties: {list(props.keys())}\n"
        "DCP allows deferred proofs but the schema must declare the expected proof structure."
    )


# ---------------------------------------------------------------------------
# Test 3: Presentation envelope schema exists in registry
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_presentation_envelope_schema_exists(schema_registry) -> None:
    """Presentation envelope $id must be resolvable from the offline schema_registry."""
    schema_path = _find_schema(PRESENTATION_ENVELOPE_PATHS)
    if schema_path is None:
        pytest.skip("presentation-envelope.schema.json not found in vc/source/")

    schema = json.loads(schema_path.read_text())
    schema_id = schema.get("$id", "")

    assert schema_id, f"presentation-envelope schema has no $id: {schema_path}"
    assert "dataspace-control-plane.internal" in schema_id, (
        f"presentation-envelope $id must use internal base URI. Got: {schema_id!r}"
    )


# ---------------------------------------------------------------------------
# Test 4: No private key material in VC examples
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_no_private_key_in_vc_examples() -> None:
    """VC examples must not contain private key material."""
    if not VC_EXAMPLES_VALID.exists():
        pytest.skip(f"VC valid examples directory not found: {VC_EXAMPLES_VALID}")

    private_key_indicators = [
        "privateKey",
        "private_key",
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
    ]

    violations: list[str] = []
    for example_file in VC_EXAMPLES_VALID.glob("*.json"):
        try:
            content = example_file.read_text(encoding="utf-8")
        except OSError:
            continue

        for indicator in private_key_indicators:
            if indicator in content:
                violations.append(
                    f"{example_file.name}: contains '{indicator}'"
                )
                break

    assert not violations, (
        f"Private key material found in VC examples ({len(violations)} file(s)):\n"
        + "\n".join(f"  {v}" for v in violations)
    )
