"""
tests/unit/procedures/messages/test_message_validation.py
Unit tests for message schema contracts used by procedures.

Tests:
  1. usage-record schema has immutable recordId (present in required)
  2. CloudEvents envelope specversion has const: "1.0"
  3. usage-record schema is independent of CloudEvents transport

Uses live schema files from schemas/metering/source/.
Marker: unit
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
METERING_SRC = REPO_ROOT / "schemas" / "metering" / "source"

USAGE_RECORD_PATH = METERING_SRC / "business" / "usage-record.schema.json"
CLOUDEVENTS_PATH = METERING_SRC / "transport" / "cloudevents-envelope.schema.json"


@pytest.fixture(scope="module")
def usage_record_schema() -> dict:
    if not USAGE_RECORD_PATH.exists():
        pytest.skip(f"usage-record schema not found: {USAGE_RECORD_PATH}")
    return json.loads(USAGE_RECORD_PATH.read_text())


@pytest.fixture(scope="module")
def cloudevents_schema() -> dict:
    if not CLOUDEVENTS_PATH.exists():
        pytest.skip(f"cloudevents-envelope schema not found: {CLOUDEVENTS_PATH}")
    return json.loads(CLOUDEVENTS_PATH.read_text())


# ---------------------------------------------------------------------------
# Test 1: recordId is in required fields (immutable once set)
# ---------------------------------------------------------------------------


def test_usage_record_schema_has_immutable_record_id(usage_record_schema: dict) -> None:
    """
    usage-record.schema.json must declare 'recordId' in its required array.

    recordId is the globally unique, stable record identifier — it must be
    set on creation and never changed, making it effectively immutable.
    """
    required = usage_record_schema.get("required", [])
    assert "recordId" in required, (
        f"'recordId' must be in usage-record required array for immutability guarantee.\n"
        f"Current required: {required}"
    )


# ---------------------------------------------------------------------------
# Test 2: CloudEvents specversion has const: "1.0"
# ---------------------------------------------------------------------------


def test_cloudevents_specversion_is_locked(cloudevents_schema: dict) -> None:
    """
    cloudevents-envelope.schema.json must lock specversion to const '1.0'.

    This prevents accidental CloudEvents version drift in metering events.
    """
    props = cloudevents_schema.get("properties", {})
    specversion = props.get("specversion", {})
    const_value = specversion.get("const")

    assert const_value == "1.0", (
        f"cloudevents-envelope specversion must have const: '1.0', got: {const_value!r}"
    )


# ---------------------------------------------------------------------------
# Test 3: usage-record is independent of CloudEvents transport
# ---------------------------------------------------------------------------


def test_usage_record_independent_of_transport(usage_record_schema: dict) -> None:
    """
    usage-record.schema.json must not contain CloudEvents-specific fields.

    The business record must be transport-neutral — CloudEvents wrapping happens
    at the transport layer in cloudevents-envelope, not in the record itself.
    """
    schema_str = json.dumps(usage_record_schema)

    assert "cloudevents" not in schema_str.lower(), (
        "usage-record schema must not reference CloudEvents — "
        "transport concerns belong in cloudevents-envelope schema"
    )
    assert '"specversion"' not in schema_str, (
        "usage-record schema must not contain 'specversion' — "
        "that is a CloudEvents transport field"
    )
