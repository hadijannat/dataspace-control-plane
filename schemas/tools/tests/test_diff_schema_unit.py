"""
schemas/tools/tests/test_diff_schema_unit.py
Unit tests for the pure _changes() diffing logic in schemas/tools/diff_schema.py.

conftest.py inserts schemas/tools/ into sys.path so bare-module imports work.
"""
from __future__ import annotations

import pytest

from diff_schema import _changes


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _breaking(changes: list[dict]) -> list[dict]:
    return [c for c in changes if c.get("breaking")]


def _non_breaking(changes: list[dict]) -> list[dict]:
    return [c for c in changes if not c.get("breaking")]


def _kinds(changes: list[dict]) -> list[str]:
    return [c["kind"] for c in changes]


# ---------------------------------------------------------------------------
# Identical schemas → no changes
# ---------------------------------------------------------------------------

def test_identical_empty_schemas_produce_no_changes() -> None:
    assert _changes({}, {}) == []


def test_identical_non_empty_schemas_produce_no_changes() -> None:
    schema = {
        "type": "object",
        "properties": {"id": {"type": "string"}},
        "required": ["id"],
    }
    assert _changes(schema, schema) == []


# ---------------------------------------------------------------------------
# Type mismatch at top level
# ---------------------------------------------------------------------------

def test_type_change_dict_to_list_is_breaking() -> None:
    changes = _changes({"type": "object"}, ["not", "a", "dict"])
    assert any(c["kind"] == "type_change" for c in changes)
    assert all(c["breaking"] for c in changes)


def test_type_change_string_to_dict_is_breaking() -> None:
    changes = _changes("hello", {"type": "string"})
    assert len(changes) == 1
    assert changes[0]["kind"] == "type_change"
    assert changes[0]["breaking"] is True


# ---------------------------------------------------------------------------
# Non-dict scalars → value_change (non-breaking)
# ---------------------------------------------------------------------------

def test_scalar_value_change_is_non_breaking() -> None:
    changes = _changes("old_value", "new_value")
    assert len(changes) == 1
    assert changes[0]["kind"] == "value_change"
    assert changes[0]["breaking"] is False


def test_identical_scalars_produce_no_changes() -> None:
    assert _changes(42, 42) == []
    assert _changes("same", "same") == []
    assert _changes(True, True) == []


# ---------------------------------------------------------------------------
# required fields
# ---------------------------------------------------------------------------

def test_required_field_added_is_breaking() -> None:
    old = {"type": "object", "required": ["id"]}
    new = {"type": "object", "required": ["id", "name"]}
    changes = _changes(old, new)
    kinds = _kinds(changes)
    assert "required_added" in kinds
    breaking = _breaking(changes)
    assert any(c["field"] == "name" for c in breaking)


def test_required_field_removed_is_non_breaking() -> None:
    old = {"type": "object", "required": ["id", "name"]}
    new = {"type": "object", "required": ["id"]}
    changes = _changes(old, new)
    kinds = _kinds(changes)
    assert "required_removed" in kinds
    nb = _non_breaking(changes)
    assert any(c["field"] == "name" for c in nb)


def test_required_fields_unchanged_produces_no_required_changes() -> None:
    schema = {"type": "object", "required": ["id"]}
    changes = _changes(schema, schema)
    assert not any("required" in c["kind"] for c in changes)


# ---------------------------------------------------------------------------
# properties
# ---------------------------------------------------------------------------

def test_property_removed_is_breaking() -> None:
    old = {"properties": {"id": {"type": "string"}, "name": {"type": "string"}}}
    new = {"properties": {"id": {"type": "string"}}}
    changes = _changes(old, new)
    assert any(c["kind"] == "property_removed" for c in changes)
    assert all(c["breaking"] for c in _breaking(changes))


def test_property_added_is_non_breaking() -> None:
    old = {"properties": {"id": {"type": "string"}}}
    new = {"properties": {"id": {"type": "string"}, "name": {"type": "string"}}}
    changes = _changes(old, new)
    assert any(c["kind"] == "property_added" for c in changes)
    added = [c for c in changes if c["kind"] == "property_added"]
    assert all(not c["breaking"] for c in added)


def test_property_recursed_into_for_nested_changes() -> None:
    old = {"properties": {"id": {"type": "string"}}}
    new = {"properties": {"id": {"type": "integer"}}}
    changes = _changes(old, new)
    assert any(c["kind"] == "type_narrowed" for c in changes)
    assert any(c["path"].endswith("/id/type") for c in changes)


# ---------------------------------------------------------------------------
# type narrowing
# ---------------------------------------------------------------------------

def test_type_narrowed_string_to_integer_is_breaking() -> None:
    old = {"type": "string"}
    new = {"type": "integer"}
    changes = _changes(old, new)
    assert any(c["kind"] == "type_narrowed" and c["breaking"] for c in changes)


def test_type_field_unchanged_produces_no_type_narrowed() -> None:
    schema = {"type": "string"}
    assert not any(c["kind"] == "type_narrowed" for c in _changes(schema, schema))


def test_type_narrowed_not_emitted_when_only_one_side_has_type() -> None:
    """If old has no type but new does (or vice versa), type_narrowed is not emitted."""
    changes = _changes({}, {"type": "string"})
    assert not any(c["kind"] == "type_narrowed" for c in changes)


# ---------------------------------------------------------------------------
# enum
# ---------------------------------------------------------------------------

def test_enum_values_removed_is_breaking() -> None:
    old = {"enum": ["a", "b", "c"]}
    new = {"enum": ["a", "b"]}
    changes = _changes(old, new)
    removed_changes = [c for c in changes if c["kind"] == "enum_values_removed"]
    assert len(removed_changes) == 1
    assert removed_changes[0]["breaking"] is True
    assert "c" in removed_changes[0]["removed"]


def test_enum_values_added_is_non_breaking() -> None:
    old = {"enum": ["a", "b"]}
    new = {"enum": ["a", "b", "c"]}
    changes = _changes(old, new)
    added_changes = [c for c in changes if c["kind"] == "enum_values_added"]
    assert len(added_changes) == 1
    assert added_changes[0]["breaking"] is False
    assert "c" in added_changes[0]["added"]


def test_enum_no_change_when_identical() -> None:
    schema = {"enum": ["x", "y"]}
    assert not any("enum" in c["kind"] for c in _changes(schema, schema))


def test_enum_not_reported_when_old_enum_empty() -> None:
    """When old has no enum, adding one is not flagged as enum_values_removed."""
    old = {"type": "string"}
    new = {"type": "string", "enum": ["a", "b"]}
    changes = _changes(old, new)
    assert not any(c["kind"] == "enum_values_removed" for c in changes)


# ---------------------------------------------------------------------------
# numeric bounds
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bound,old_val,new_val,expected_breaking", [
    ("minimum", 0, 5, True),     # increased → breaking
    ("minimum", 5, 0, False),    # decreased → non-breaking
    ("minLength", 1, 10, True),  # increased → breaking
    ("minLength", 10, 1, False), # decreased → non-breaking
    ("maximum", 100, 50, True),  # decreased → breaking
    ("maximum", 50, 100, False), # increased → non-breaking
    ("maxLength", 255, 10, True),  # decreased → breaking
    ("maxLength", 10, 255, False), # increased → non-breaking
])
def test_numeric_bounds(bound: str, old_val: int, new_val: int, expected_breaking: bool) -> None:
    old = {bound: old_val}
    new = {bound: new_val}
    changes = _changes(old, new)
    bound_changes = [c for c in changes if bound in c["kind"]]
    assert len(bound_changes) == 1
    assert bound_changes[0]["breaking"] is expected_breaking


def test_numeric_bound_no_change_when_identical() -> None:
    schema = {"minimum": 0, "maximum": 100}
    assert _changes(schema, schema) == []


# ---------------------------------------------------------------------------
# additionalProperties
# ---------------------------------------------------------------------------

def test_additional_properties_set_to_false_is_breaking() -> None:
    old = {"type": "object"}
    new = {"type": "object", "additionalProperties": False}
    changes = _changes(old, new)
    ap_changes = [c for c in changes if c["kind"] == "additional_properties_changed"]
    assert len(ap_changes) == 1
    assert ap_changes[0]["breaking"] is True


def test_additional_properties_relaxed_is_non_breaking() -> None:
    old = {"type": "object", "additionalProperties": False}
    new = {"type": "object", "additionalProperties": True}
    changes = _changes(old, new)
    ap_changes = [c for c in changes if c["kind"] == "additional_properties_changed"]
    assert len(ap_changes) == 1
    assert ap_changes[0]["breaking"] is False


def test_additional_properties_unchanged_produces_no_change() -> None:
    schema = {"type": "object", "additionalProperties": False}
    assert not any(c["kind"] == "additional_properties_changed" for c in _changes(schema, schema))


# ---------------------------------------------------------------------------
# pattern
# ---------------------------------------------------------------------------

def test_pattern_changed_is_always_breaking() -> None:
    old = {"type": "string", "pattern": "^[a-z]+$"}
    new = {"type": "string", "pattern": "^[A-Za-z]+$"}
    changes = _changes(old, new)
    pat_changes = [c for c in changes if c["kind"] == "pattern_changed"]
    assert len(pat_changes) == 1
    assert pat_changes[0]["breaking"] is True


def test_pattern_unchanged_produces_no_change() -> None:
    schema = {"type": "string", "pattern": "^[a-z]+$"}
    assert not any(c["kind"] == "pattern_changed" for c in _changes(schema, schema))


# ---------------------------------------------------------------------------
# path construction
# ---------------------------------------------------------------------------

def test_path_prefix_propagated_in_nested_changes() -> None:
    old = {"properties": {"meta": {"properties": {"id": {"type": "string"}}}}}
    new = {"properties": {"meta": {"properties": {}}}}
    changes = _changes(old, new, path="#/root")
    removed = [c for c in changes if c["kind"] == "property_removed"]
    assert any("meta" in c["path"] and "id" in c["path"] for c in removed)
