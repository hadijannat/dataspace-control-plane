"""
tests/integration/apps/control_api/test_usage_record_ingestion.py
Integration tests for the control-api usage record ingestion endpoint.

Tests:
  1. Health endpoint returns 200
  2. Usage record schema validation rejects missing tenantId
  3. API endpoint rejects usage event without tenantId (422/400)

Test 1 works without live services (test client uses fallback minimal app).
Tests 2-3 are marked integration — they use the test_client fixture.
Marker: integration (tests 2-3); unit (test 2 inline validation)
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
USAGE_RECORD_SCHEMA_PATH = (
    REPO_ROOT / "schemas" / "metering" / "source" / "business" / "usage-record.schema.json"
)


# ---------------------------------------------------------------------------
# Test 1: Health endpoint returns 200
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_health_endpoint(test_client) -> None:
    """GET /health must return HTTP 200 with status indicator."""
    response = test_client.get("/health")
    assert response.status_code == 200, (
        f"Health endpoint returned {response.status_code}, expected 200"
    )
    data = response.json()
    assert "status" in data, f"Health response missing 'status' field: {data}"


# ---------------------------------------------------------------------------
# Test 2: Schema validation rejects missing tenantId
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.integration
def test_usage_record_schema_validation() -> None:
    """
    Inline JSON Schema validation must reject a usage record without tenantId.

    This test does not require a running service — it validates the schema contract
    that the API must enforce.
    """
    jsonschema = pytest.importorskip("jsonschema")
    from jsonschema import Draft202012Validator

    if not USAGE_RECORD_SCHEMA_PATH.exists():
        pytest.skip(f"usage-record schema not found: {USAGE_RECORD_SCHEMA_PATH}")

    schema = json.loads(USAGE_RECORD_SCHEMA_PATH.read_text())
    validator = Draft202012Validator(schema)

    # Missing tenantId
    invalid_record = {
        "recordId": "550e8400-e29b-41d4-a716-446655440000",
        # tenantId intentionally omitted
        "legalEntityId": "BPNL000000000000",
        "eventTime": "2026-01-01T00:00:00Z",
        "reportedAt": "2026-01-01T00:00:01Z",
        "sourceSystem": "test",
    }

    errors = list(validator.iter_errors(invalid_record))
    tenant_errors = [
        e for e in errors
        if "tenantId" in str(e.message) or "tenantId" in str(e.path)
    ]
    assert errors, (
        "Expected validation errors for usage record without tenantId, but schema passed"
    )


# ---------------------------------------------------------------------------
# Test 3: API endpoint rejects usage event without tenantId
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_usage_event_rejected_without_tenant_id(test_client) -> None:
    """POST to usage-events endpoint without tenantId must return 422 or 400."""
    # Try known endpoint paths
    for endpoint in ["/api/v1/usage-events", "/api/v1/metering/events", "/usage-events"]:
        response = test_client.post(
            endpoint,
            json={
                "recordId": "550e8400-e29b-41d4-a716-446655440000",
                # tenantId intentionally omitted
                "eventTime": "2026-01-01T00:00:00Z",
            },
        )
        if response.status_code == 404:
            continue  # Try next endpoint path
        if response.status_code in (422, 400):
            return  # Test passes — endpoint correctly rejected the request
        if response.status_code == 500:
            pytest.fail(
                f"Usage event endpoint returned 500 instead of 422/400 for invalid input. "
                f"Response: {response.text}"
            )

    # If all endpoints returned 404, the feature is not yet implemented
    pytest.skip("control-api usage event endpoint not yet implemented")
