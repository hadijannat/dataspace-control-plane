"""Domain invariants for the schema_mapping domain."""
from __future__ import annotations

from dataspace_control_plane_core.domains._shared.errors import ValidationError


def require_at_least_one_rule(mapping: object) -> None:
    """Raise ValidationError if the mapping has no rules."""
    from .aggregates import SchemaMapping
    assert isinstance(mapping, SchemaMapping)
    if not mapping.rules:
        raise ValidationError(
            f"SchemaMapping {mapping.id} must have at least one rule",
            {"mapping_id": str(mapping.id)},
        )


def require_no_duplicate_source_paths(mapping: object) -> None:
    """Raise ValidationError if any source_path appears more than once in the rule list."""
    from .aggregates import SchemaMapping
    assert isinstance(mapping, SchemaMapping)
    seen: set[str] = set()
    for rule in mapping.rules:
        if rule.source_path in seen:
            raise ValidationError(
                f"Duplicate source_path '{rule.source_path}' in SchemaMapping {mapping.id}",
                {"mapping_id": str(mapping.id), "source_path": rule.source_path},
            )
        seen.add(rule.source_path)
