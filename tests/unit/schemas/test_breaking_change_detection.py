"""
tests/unit/schemas/test_breaking_change_detection.py
Regression suite for schemas/tools/diff_schema.py.

Locks the breaking-change classification logic against a golden set of
schema mutation cases. If diff_schema.py stops detecting a known-breaking
mutation, this suite fails — protecting consumers from silent regressions.

Run:
    pytest tests/unit/schemas/test_breaking_change_detection.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add schemas/tools/ to path so diff_schema can be imported directly
_TOOLS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "schemas" / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

import diff_schema  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify(old: dict, new: dict) -> tuple[list[dict], list[dict]]:
    """Return (breaking_changes, non_breaking_changes) for the given schema pair."""
    all_changes = diff_schema._changes(old, new)
    breaking = [c for c in all_changes if c.get("breaking")]
    non_breaking = [c for c in all_changes if not c.get("breaking")]
    return breaking, non_breaking


# ---------------------------------------------------------------------------
# Breaking change cases
# ---------------------------------------------------------------------------

def test_required_field_added_is_breaking() -> None:
    """Adding a field to `required` is breaking — existing instances may lack it."""
    old = {"type": "object", "properties": {"a": {}, "b": {}}, "required": ["a"]}
    new = {"type": "object", "properties": {"a": {}, "b": {}}, "required": ["a", "b"]}
    breaking, _ = _classify(old, new)
    kinds = {c["kind"] for c in breaking}
    assert "required_added" in kinds, f"Expected required_added in breaking changes, got {kinds}"


def test_property_removed_is_breaking() -> None:
    """Removing a property that was present is breaking — consumers may reference it."""
    old = {"type": "object", "properties": {"a": {}, "b": {}}}
    new = {"type": "object", "properties": {"a": {}}}
    breaking, _ = _classify(old, new)
    kinds = {c["kind"] for c in breaking}
    assert "property_removed" in kinds, f"Expected property_removed in breaking changes, got {kinds}"


def test_enum_value_removed_is_breaking() -> None:
    """Removing an enum value is breaking — existing instances may use it."""
    old = {"enum": ["active", "pending", "closed"]}
    new = {"enum": ["active", "closed"]}
    breaking, _ = _classify(old, new)
    kinds = {c["kind"] for c in breaking}
    assert "enum_values_removed" in kinds, f"Expected enum_values_removed in breaking changes, got {kinds}"


def test_type_narrowed_is_breaking() -> None:
    """Changing type from a broader type to a narrower one is breaking."""
    old = {"type": "string", "properties": {}}
    new = {"type": "integer", "properties": {}}
    breaking, _ = _classify(old, new)
    kinds = {c["kind"] for c in breaking}
    assert "type_narrowed" in kinds, f"Expected type_narrowed in breaking changes, got {kinds}"


def test_additional_properties_closed_is_breaking() -> None:
    """Setting additionalProperties: false on a previously open schema is breaking."""
    old = {"type": "object", "properties": {"a": {}}}
    new = {"type": "object", "properties": {"a": {}}, "additionalProperties": False}
    breaking, _ = _classify(old, new)
    kinds = {c["kind"] for c in breaking}
    assert "additional_properties_changed" in kinds, (
        f"Expected additional_properties_changed in breaking changes, got {kinds}"
    )


def test_minimum_increased_is_breaking() -> None:
    """Increasing the minimum constraint narrows the valid range — breaking."""
    old = {"type": "number", "minimum": 0}
    new = {"type": "number", "minimum": 10}
    breaking, _ = _classify(old, new)
    kinds = {c["kind"] for c in breaking}
    assert "minimum_changed" in kinds, f"Expected minimum_changed in breaking changes, got {kinds}"


def test_pattern_changed_is_breaking() -> None:
    """Any change to a pattern is classified as potentially breaking."""
    old = {"type": "string", "pattern": "^[a-z]+$"}
    new = {"type": "string", "pattern": "^[a-zA-Z]+$"}
    breaking, _ = _classify(old, new)
    kinds = {c["kind"] for c in breaking}
    assert "pattern_changed" in kinds, f"Expected pattern_changed in breaking changes, got {kinds}"


# ---------------------------------------------------------------------------
# Non-breaking change cases
# ---------------------------------------------------------------------------

def test_required_field_removed_is_non_breaking() -> None:
    """Removing a field from `required` is non-breaking — existing instances still validate."""
    old = {"type": "object", "properties": {"a": {}, "b": {}}, "required": ["a", "b"]}
    new = {"type": "object", "properties": {"a": {}, "b": {}}, "required": ["a"]}
    breaking, non_breaking = _classify(old, new)
    assert not breaking, f"Expected no breaking changes, got {[c['kind'] for c in breaking]}"
    kinds = {c["kind"] for c in non_breaking}
    assert "required_removed" in kinds


def test_optional_property_added_is_non_breaking() -> None:
    """Adding an optional property is non-breaking — does not affect existing instances."""
    old = {"type": "object", "properties": {"a": {}}}
    new = {"type": "object", "properties": {"a": {}, "b": {}}}
    breaking, non_breaking = _classify(old, new)
    assert not breaking, f"Expected no breaking changes, got {[c['kind'] for c in breaking]}"
    kinds = {c["kind"] for c in non_breaking}
    assert "property_added" in kinds


def test_enum_value_added_is_non_breaking() -> None:
    """Adding enum values is non-breaking — existing instances still match."""
    old = {"enum": ["active", "closed"]}
    new = {"enum": ["active", "pending", "closed"]}
    breaking, non_breaking = _classify(old, new)
    assert not breaking, f"Expected no breaking changes, got {[c['kind'] for c in breaking]}"
    kinds = {c["kind"] for c in non_breaking}
    assert "enum_values_added" in kinds


def test_minimum_decreased_is_non_breaking() -> None:
    """Decreasing the minimum constraint widens the valid range — non-breaking."""
    old = {"type": "number", "minimum": 10}
    new = {"type": "number", "minimum": 0}
    _, non_breaking = _classify(old, new)
    assert non_breaking, "Expected at least one non-breaking change"
    kinds = {c["kind"] for c in non_breaking}
    assert "minimum_changed" in kinds


def test_no_changes_produces_empty_results() -> None:
    """Identical schemas produce no changes at all."""
    schema = {
        "type": "object",
        "properties": {"id": {"type": "string"}},
        "required": ["id"],
    }
    breaking, non_breaking = _classify(schema, schema)
    assert not breaking
    assert not non_breaking


# ---------------------------------------------------------------------------
# Golden schema regression: usage-record
# ---------------------------------------------------------------------------

def test_usage_record_required_field_addition_detected() -> None:
    """
    Regression lock: if usage-record.schema.json ever adds a new required field,
    diff_schema.py must detect it as a breaking change.

    This test uses an inline snapshot of the required fields from
    schemas/metering/source/business/usage-record.schema.json as the 'old'
    version, then adds a new required field to the 'new' version.
    """
    # Snapshot of usage-record required fields (current as of schemas Wave 1)
    golden_required = [
        "recordId", "tenantId", "legalEntityId", "agreementRef",
        "counterpartyRef", "dimensions", "eventTime", "reportedAt", "sourceSystem",
    ]
    old = {"type": "object", "properties": {k: {} for k in golden_required}, "required": golden_required}
    new_required = golden_required + ["newRequiredField"]
    new = {"type": "object", "properties": {k: {} for k in new_required}, "required": new_required}

    breaking, _ = _classify(old, new)
    kinds = {c["kind"] for c in breaking}
    assert "required_added" in kinds
    # Confirm it's specifically the new field
    new_required_changes = [c for c in breaking if c.get("kind") == "required_added"]
    added_fields = {c["field"] for c in new_required_changes}
    assert "newRequiredField" in added_fields
