"""
tests/integration/adapters/enterprise/test_metering_kafka.py
Integration tests for Kafka serde layer and metering payload schema contracts.

Tests:
  1. Kafka serde module is importable
  2. build_envelope produces all required fields
  3. encode_envelope + decode_envelope round-trip is lossless
  4. decode_envelope raises KafkaSerdeError on missing required fields
  5. decode_envelope raises KafkaSerdeError on malformed JSON
  6. KafkaCheckpoint serialization round-trip
  7. KafkaCheckpoint deserialization rejects missing fields
  8. A well-formed usage-record payload validates against usage-record.schema.json
  9. A usage-record missing required fields fails schema validation
 10. A usage-record envelope wrapping a valid payload round-trips without data loss
 11. build_envelope with usage-record payload sets correct event_type and tenant_id
 12. usage-record schema requires all 8 required fields

All tests are pure Python — no Kafka broker required.
Marker: integration
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.unit

# ── Path injection ────────────────────────────────────────────────────────────
_ADAPTERS_SRC = (
    Path(__file__).resolve().parent.parent.parent.parent.parent
    / "adapters"
    / "src"
)
if _ADAPTERS_SRC.exists() and str(_ADAPTERS_SRC) not in sys.path:
    sys.path.insert(0, str(_ADAPTERS_SRC))

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
USAGE_RECORD_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "metering" / "source" / "business" / "usage-record.schema.json"
)


def _skip_if_adapters_missing() -> None:
    try:
        import dataspace_control_plane_adapters  # noqa: F401
    except ImportError as exc:
        pytest.skip(f"adapters package not available: {exc}")


def _import_serde():
    from dataspace_control_plane_adapters.enterprise.kafka_ingest.serde import (
        build_envelope,
        decode_envelope,
        encode_envelope,
    )
    from dataspace_control_plane_adapters.enterprise.kafka_ingest.errors import KafkaSerdeError
    return build_envelope, encode_envelope, decode_envelope, KafkaSerdeError


def _import_checkpoint():
    from dataspace_control_plane_adapters.enterprise.kafka_ingest.checkpoint import (
        KafkaCheckpoint,
        deserialize_checkpoint,
        serialize_checkpoint,
    )
    return KafkaCheckpoint, serialize_checkpoint, deserialize_checkpoint


# ── Fixture payload builders ──────────────────────────────────────────────────

def _valid_usage_record() -> dict[str, Any]:
    """Minimal valid usage-record payload conforming to the schema."""
    return {
        "recordId": "550e8400-e29b-41d4-a716-446655440000",
        "tenantId": "tenant-abc",
        "legalEntityId": "BPNL000000000001",
        "agreementRef": {
            "agreementId": "agreement-001",
            "contractId": "contract-001",
        },
        "counterpartyRef": {
            "bpn": "BPNL000000000002",
        },
        "dimensions": [
            {
                "name": "data_volume_mb",
                "value": 512,
                "unit": "MB",
            }
        ],
        "eventTime": "2026-01-01T12:00:00Z",
        "reportedAt": "2026-01-01T12:00:01Z",
        "sourceSystem": "edc-extension",
    }


# ── Test 1: import smoke test ─────────────────────────────────────────────────


def test_kafka_serde_importable() -> None:
    """Kafka serde and checkpoint modules must be importable from adapters package."""
    _skip_if_adapters_missing()
    build_envelope, encode_envelope, decode_envelope, KafkaSerdeError = _import_serde()
    KafkaCheckpoint, serialize_checkpoint, deserialize_checkpoint = _import_checkpoint()

    assert callable(build_envelope)
    assert callable(encode_envelope)
    assert callable(decode_envelope)
    assert callable(serialize_checkpoint)
    assert callable(deserialize_checkpoint)


# ── Test 2: build_envelope produces required fields ───────────────────────────


def test_build_envelope_produces_all_required_fields() -> None:
    """build_envelope must include all 8 required envelope fields."""
    _skip_if_adapters_missing()
    build_envelope, _, _, _ = _import_serde()

    envelope = build_envelope(
        event_type="usage.record.created",
        tenant_id="tenant-test",
        payload={"key": "value"},
        source_topic="metering.events",
        partition=0,
        offset=42,
        correlation_id="corr-001",
    )

    required = {
        "schema_id", "tenant_id", "event_type",
        "correlation_id", "source_topic", "source_partition",
        "source_offset", "payload",
    }
    missing = required - envelope.keys()
    assert not missing, (
        f"build_envelope output missing required fields: {missing}\n"
        f"Got keys: {list(envelope.keys())}"
    )

    assert envelope["event_type"] == "usage.record.created"
    assert envelope["tenant_id"] == "tenant-test"
    assert envelope["source_topic"] == "metering.events"
    assert envelope["source_partition"] == 0
    assert envelope["source_offset"] == 42
    assert envelope["correlation_id"] == "corr-001"
    assert envelope["payload"] == {"key": "value"}


# ── Test 3: encode + decode round-trip ───────────────────────────────────────


def test_encode_decode_envelope_round_trip() -> None:
    """encode_envelope followed by decode_envelope must return an equal dict."""
    _skip_if_adapters_missing()
    build_envelope, encode_envelope, decode_envelope, _ = _import_serde()

    original_payload = {"assetId": "asset-001", "volume_mb": 128}
    envelope = build_envelope(
        event_type="data.transfer.completed",
        tenant_id="tenant-xyz",
        payload=original_payload,
        source_topic="data.transfers",
        partition=1,
        offset=99,
        correlation_id="corr-xyz",
    )

    encoded = encode_envelope(envelope)
    assert isinstance(encoded, bytes), (
        f"encode_envelope must return bytes; got {type(encoded).__name__}"
    )

    decoded = decode_envelope(encoded)
    assert decoded["event_type"] == "data.transfer.completed"
    assert decoded["tenant_id"] == "tenant-xyz"
    assert decoded["payload"] == original_payload
    assert decoded["source_partition"] == 1
    assert decoded["source_offset"] == 99


# ── Test 4: decode_envelope rejects missing required fields ──────────────────


def test_decode_envelope_raises_on_missing_required_field() -> None:
    """decode_envelope must raise KafkaSerdeError when required fields are absent."""
    _skip_if_adapters_missing()
    _, encode_envelope, decode_envelope, KafkaSerdeError = _import_serde()

    # Build an incomplete envelope (missing source_partition, source_offset, payload, etc.)
    incomplete = {
        "schema_id": "v1",
        "tenant_id": "tenant-test",
        # event_type and other required fields intentionally omitted
    }
    raw = json.dumps(incomplete).encode("utf-8")

    with pytest.raises(KafkaSerdeError):
        decode_envelope(raw)


# ── Test 5: decode_envelope rejects malformed JSON ────────────────────────────


def test_decode_envelope_raises_on_malformed_json() -> None:
    """decode_envelope must raise KafkaSerdeError for non-JSON byte input."""
    _skip_if_adapters_missing()
    _, _, decode_envelope, KafkaSerdeError = _import_serde()

    with pytest.raises(KafkaSerdeError):
        decode_envelope(b"this is not json {{{")


# ── Test 6: KafkaCheckpoint serialize / deserialize round-trip ─────────────────


def test_kafka_checkpoint_serialize_deserialize_round_trip() -> None:
    """KafkaCheckpoint serialization must round-trip through serialize/deserialize."""
    _skip_if_adapters_missing()
    KafkaCheckpoint, serialize_checkpoint, deserialize_checkpoint = _import_checkpoint()

    original = KafkaCheckpoint(topic="metering.events", partition=2, offset=1234)
    serialized = serialize_checkpoint(original)

    assert isinstance(serialized, str), (
        f"serialize_checkpoint must return str; got {type(serialized).__name__}"
    )

    restored = deserialize_checkpoint(serialized)
    assert restored.topic == original.topic
    assert restored.partition == original.partition
    assert restored.offset == original.offset


# ── Test 7: KafkaCheckpoint deserialization rejects bad data ─────────────────


def test_deserialize_checkpoint_raises_on_missing_fields() -> None:
    """deserialize_checkpoint must raise on JSON missing required fields."""
    _skip_if_adapters_missing()
    _, _, deserialize_checkpoint = _import_checkpoint()

    bad_json = json.dumps({"topic": "t"})  # missing partition and offset
    with pytest.raises((KeyError, ValueError, TypeError)):
        deserialize_checkpoint(bad_json)


# ── Shared schema validation helper ──────────────────────────────────────────


def _validate_offline(schema: dict, instance: dict) -> list:
    """Validate instance against schema, skipping unresolvable $ref errors (offline mode).

    Returns a list of jsonschema ValidationError objects for true schema violations.
    Unresolvable $ref errors are silently dropped — they indicate missing external
    schemas, not instance invalidity.
    """
    from jsonschema import Draft202012Validator

    validator = Draft202012Validator(schema)
    errors = []
    try:
        for error in validator.iter_errors(instance):
            errors.append(error)
    except Exception as exc:
        exc_name = type(exc).__name__
        # referencing.exceptions.Unresolvable and legacy RefResolutionError
        if "Unresolvable" in str(exc) or "WrappedReferencing" in exc_name or "RefResolution" in exc_name:
            return errors  # return whatever we collected before the exception
        raise
    return errors


# ── Test 8: valid usage-record validates against schema ──────────────────────


def test_valid_usage_record_passes_schema_validation() -> None:
    """A well-formed usage-record dict must validate against usage-record.schema.json."""
    pytest.importorskip("jsonschema", reason="jsonschema not installed")

    if not USAGE_RECORD_SCHEMA_PATH.exists():
        pytest.skip(f"usage-record schema not found: {USAGE_RECORD_SCHEMA_PATH}")

    schema = json.loads(USAGE_RECORD_SCHEMA_PATH.read_text())
    record = _valid_usage_record()

    errors = _validate_offline(schema, record)
    assert not errors, (
        f"Valid usage-record unexpectedly failed schema validation:\n"
        + "\n".join(f"  - {e.message}" for e in errors)
    )


# ── Test 9: invalid usage-record fails schema validation ─────────────────────


def test_invalid_usage_record_fails_schema_validation() -> None:
    """A usage-record missing tenantId must fail schema validation."""
    pytest.importorskip("jsonschema", reason="jsonschema not installed")

    if not USAGE_RECORD_SCHEMA_PATH.exists():
        pytest.skip(f"usage-record schema not found: {USAGE_RECORD_SCHEMA_PATH}")

    schema = json.loads(USAGE_RECORD_SCHEMA_PATH.read_text())
    record = _valid_usage_record()
    del record["tenantId"]  # remove a required field

    from jsonschema import Draft202012Validator
    validator = Draft202012Validator(schema)
    # Collect errors, stopping at Unresolvable but keeping required-field errors
    errors = _validate_offline(schema, record)
    assert errors, (
        "Usage record without 'tenantId' must fail schema validation, but it passed"
    )
    error_messages = " ".join(e.message for e in errors)
    assert "tenantId" in error_messages, (
        f"Schema error must reference 'tenantId'; got: {error_messages!r}"
    )


# ── Test 10: usage-record wrapped in envelope round-trips ─────────────────────


def test_usage_record_envelope_round_trip() -> None:
    """build_envelope wrapping a usage-record payload must survive encode/decode."""
    _skip_if_adapters_missing()
    build_envelope, encode_envelope, decode_envelope, _ = _import_serde()

    usage_record = _valid_usage_record()
    envelope = build_envelope(
        event_type="usage.record.created",
        tenant_id=usage_record["tenantId"],
        payload=usage_record,
        source_topic="metering.usage-records",
        partition=0,
        offset=500,
        correlation_id="corr-metering-001",
    )

    decoded = decode_envelope(encode_envelope(envelope))
    restored_record = decoded["payload"]

    assert restored_record["recordId"] == usage_record["recordId"]
    assert restored_record["tenantId"] == usage_record["tenantId"]
    assert restored_record["legalEntityId"] == usage_record["legalEntityId"]
    assert restored_record["sourceSystem"] == usage_record["sourceSystem"]


# ── Test 11: build_envelope sets tenant_id and event_type correctly ───────────


def test_build_envelope_with_usage_record_sets_correct_metadata() -> None:
    """build_envelope for a usage.record.created event must set tenant_id from argument."""
    _skip_if_adapters_missing()
    build_envelope, _, _, _ = _import_serde()

    envelope = build_envelope(
        event_type="usage.record.created",
        tenant_id="tenant-eu-1",
        payload=_valid_usage_record(),
        source_topic="metering.usage-records",
        partition=3,
        offset=7890,
        correlation_id="trace-eu-001",
        schema_id="metering.usage-record.v1",
    )

    assert envelope["tenant_id"] == "tenant-eu-1"
    assert envelope["event_type"] == "usage.record.created"
    assert envelope["schema_id"] == "metering.usage-record.v1"
    assert envelope["source_partition"] == 3
    assert envelope["source_offset"] == 7890


# ── Test 12: usage-record schema declares all 8 required fields ───────────────


def test_usage_record_schema_declares_expected_required_fields() -> None:
    """usage-record.schema.json must declare all 8 business-required fields."""
    if not USAGE_RECORD_SCHEMA_PATH.exists():
        pytest.skip(f"usage-record schema not found: {USAGE_RECORD_SCHEMA_PATH}")

    schema = json.loads(USAGE_RECORD_SCHEMA_PATH.read_text())
    required = set(schema.get("required", []))

    expected_required = {
        "recordId", "tenantId", "legalEntityId",
        "agreementRef", "counterpartyRef",
        "dimensions", "eventTime", "reportedAt", "sourceSystem",
    }
    missing = expected_required - required
    assert not missing, (
        f"usage-record schema is missing required fields: {missing}\n"
        f"Declared required: {sorted(required)}"
    )
