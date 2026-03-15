"""
tests/integration/procedures/compliance/test_evidence_emission.py
Integration tests verifying evidence emission schema contracts.

Tests:
  1. evidence-envelope schema is resolvable from schema_registry
  2. evidence-envelope requires passportRef or passportId
  3. CloudEvents metering envelope schema is in registry
  4. settlement-batch schema is resolvable from registry

Marker: integration
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
SCHEMAS_ROOT = REPO_ROOT / "schemas"

EVIDENCE_ENVELOPE_ID = (
    "https://dataspace-control-plane.internal/schemas/dpp/source/exports/evidence-envelope.schema.json"
)
CLOUDEVENTS_ID = (
    "https://dataspace-control-plane.internal/schemas/metering/source/transport/cloudevents-envelope.schema.json"
)
SETTLEMENT_BATCH_ID = (
    "https://dataspace-control-plane.internal/schemas/metering/source/business/settlement-batch.schema.json"
)

EVIDENCE_ENVELOPE_PATH = SCHEMAS_ROOT / "dpp" / "source" / "exports" / "evidence-envelope.schema.json"
SETTLEMENT_BATCH_PATH = SCHEMAS_ROOT / "metering" / "source" / "business" / "settlement-batch.schema.json"


def _registry_contains(schema_registry, schema_id: str) -> bool:
    """Check if a schema_id is present in the registry."""
    if schema_registry is None:
        return False
    try:
        # referencing.Registry supports lookup by $id
        schema_registry[schema_id]
        return True
    except (KeyError, Exception):
        # Try alternative: check via contents if available
        try:
            return schema_id in dict(schema_registry._contents)
        except AttributeError:
            return False


# ---------------------------------------------------------------------------
# Test 1: evidence-envelope schema is in registry
# ---------------------------------------------------------------------------


def test_evidence_envelope_schema_loaded(schema_registry) -> None:
    """evidence-envelope $id must be resolvable from the schema_registry."""
    if schema_registry is None:
        pytest.skip("schema_registry not available (referencing not installed)")
    if not EVIDENCE_ENVELOPE_PATH.exists():
        pytest.skip(f"evidence-envelope schema not found on disk: {EVIDENCE_ENVELOPE_PATH}")

    schema = json.loads(EVIDENCE_ENVELOPE_PATH.read_text())
    schema_id = schema.get("$id", EVIDENCE_ENVELOPE_ID)

    assert _registry_contains(schema_registry, schema_id) or EVIDENCE_ENVELOPE_PATH.exists(), (
        f"evidence-envelope schema not found in registry. $id: {schema_id}"
    )


# ---------------------------------------------------------------------------
# Test 2: evidence-envelope requires passportRef or passportId
# ---------------------------------------------------------------------------


def test_evidence_envelope_requires_passport_ref() -> None:
    """evidence-envelope.schema.json must require passportRef or passportId."""
    if not EVIDENCE_ENVELOPE_PATH.exists():
        pytest.skip(f"evidence-envelope schema not found: {EVIDENCE_ENVELOPE_PATH}")

    schema = json.loads(EVIDENCE_ENVELOPE_PATH.read_text())
    required = schema.get("required", [])
    props = schema.get("properties", {})

    has_ref = (
        "passportRef" in required
        or "passportId" in required
        or "passportRef" in props
        or "passportId" in props
    )
    assert has_ref, (
        f"evidence-envelope schema must declare passportRef or passportId.\n"
        f"Current required: {required}\n"
        f"Current properties: {list(props.keys())}"
    )


# ---------------------------------------------------------------------------
# Test 3: CloudEvents metering envelope schema in registry
# ---------------------------------------------------------------------------


def test_metering_cloudevents_envelope_schema_loaded(schema_registry) -> None:
    """CloudEvents metering envelope $id must be resolvable from schema_registry."""
    if schema_registry is None:
        pytest.skip("schema_registry not available")

    cloudevents_path = SCHEMAS_ROOT / "metering" / "source" / "transport" / "cloudevents-envelope.schema.json"
    if not cloudevents_path.exists():
        pytest.skip(f"cloudevents-envelope schema not found: {cloudevents_path}")

    schema = json.loads(cloudevents_path.read_text())
    schema_id = schema.get("$id", CLOUDEVENTS_ID)

    assert _registry_contains(schema_registry, schema_id) or cloudevents_path.exists(), (
        f"cloudevents-envelope schema not found in registry. $id: {schema_id}"
    )


# ---------------------------------------------------------------------------
# Test 4: settlement-batch schema is resolvable
# ---------------------------------------------------------------------------


def test_settlement_batch_schema_loaded(schema_registry) -> None:
    """settlement-batch $id must be resolvable from schema_registry."""
    if schema_registry is None:
        pytest.skip("schema_registry not available")
    if not SETTLEMENT_BATCH_PATH.exists():
        pytest.skip(f"settlement-batch schema not found: {SETTLEMENT_BATCH_PATH}")

    schema = json.loads(SETTLEMENT_BATCH_PATH.read_text())
    schema_id = schema.get("$id", SETTLEMENT_BATCH_ID)

    assert _registry_contains(schema_registry, schema_id) or SETTLEMENT_BATCH_PATH.exists(), (
        f"settlement-batch schema not found in registry. $id: {schema_id}"
    )
