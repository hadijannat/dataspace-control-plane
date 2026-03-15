"""
tests/unit/procedures/compensation/test_compensation_logic.py
Unit tests for compensation-related schema contracts used by procedures.

Tests:
  1. procedures/ directory exists (or skips gracefully)
  2. settlement-batch schema has a status/batchStatus property
  3. charge-statement schema references usage dimension information

Uses live schema files from schemas/metering/source/business/.
Marker: unit
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
PROCEDURES_ROOT = REPO_ROOT / "procedures"
METERING_BUSINESS = REPO_ROOT / "schemas" / "metering" / "source" / "business"

SETTLEMENT_BATCH_PATH = METERING_BUSINESS / "settlement-batch.schema.json"
CHARGE_STATEMENT_PATH = METERING_BUSINESS / "charge-statement.schema.json"


# ---------------------------------------------------------------------------
# Test 1: procedures/ directory exists
# ---------------------------------------------------------------------------


def test_compensation_schema_exists() -> None:
    """The procedures/ directory must exist at the repository root."""
    if not PROCEDURES_ROOT.exists():
        pytest.skip(
            "procedures/ directory not yet scaffolded — "
            "compensation schema test skipped"
        )
    assert PROCEDURES_ROOT.is_dir(), f"{PROCEDURES_ROOT} is not a directory"


# ---------------------------------------------------------------------------
# Test 2: settlement-batch has a status field
# ---------------------------------------------------------------------------


def test_settlement_batch_schema_has_status_field() -> None:
    """settlement-batch.schema.json must define a 'status' or 'batchStatus' property."""
    if not SETTLEMENT_BATCH_PATH.exists():
        pytest.skip(f"settlement-batch schema not found: {SETTLEMENT_BATCH_PATH}")

    schema = json.loads(SETTLEMENT_BATCH_PATH.read_text())
    props = schema.get("properties", {})

    has_status = "status" in props or "batchStatus" in props
    assert has_status, (
        f"settlement-batch schema must have 'status' or 'batchStatus' property.\n"
        f"Current properties: {list(props.keys())}"
    )

    # Verify status is in required (settlement status must be tracked)
    required = schema.get("required", [])
    assert "status" in required or "batchStatus" in required, (
        "settlement status field must be required — batch status is essential for reconciliation"
    )


# ---------------------------------------------------------------------------
# Test 3: charge-statement references usage dimension
# ---------------------------------------------------------------------------


def test_charge_statement_references_usage_dimension() -> None:
    """
    charge-statement.schema.json must reference usage dimension information.

    A charge statement must be traceable back to the usage dimensions it was
    calculated from — this ensures billing audit trails.
    """
    if not CHARGE_STATEMENT_PATH.exists():
        pytest.skip(f"charge-statement schema not found: {CHARGE_STATEMENT_PATH}")

    schema = json.loads(CHARGE_STATEMENT_PATH.read_text())
    schema_str = json.dumps(schema)

    # Check for dimension reference: either a direct property or a $ref to dimension schema
    has_dimension_ref = (
        "dimension" in schema_str.lower()
        or "usage-dimension" in schema_str
        or "usageDimension" in schema_str
        or "rated-usage" in schema_str
        or "ratedUsage" in schema_str
    )

    assert has_dimension_ref, (
        "charge-statement schema must reference usage dimension information for audit traceability.\n"
        "Expected to find 'dimension', 'usage-dimension', or 'rated-usage' reference in schema."
    )
