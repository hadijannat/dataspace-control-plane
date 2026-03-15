"""Value objects for the schema_mapping domain."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

from dataspace_control_plane_core.canonical_models.mapping import FieldMapping as CanonicalFieldMapping

from .enums import TransformType


@dataclass(frozen=True)
class MappingRule:
    """
    A single field-level mapping rule from a source path to a target path,
    with an optional transform and whether the field is required.
    """
    source_path: str
    target_path: str
    transform: TransformType
    transform_args: dict[str, str] = field(default_factory=dict)
    is_required: bool = True


@dataclass(frozen=True)
class MappingLineage:
    """
    Lineage record linking a source schema to a target schema via an ordered
    tuple of mapping rules and the timestamp the lineage was captured.
    """
    source_schema_id: str
    target_schema_id: str
    rules: tuple[MappingRule, ...]
    created_at: datetime


@dataclass(frozen=True)
class CompatibilityVector:
    """
    Summarises forward/backward compatibility of a mapping version transition
    and carries a tuple of human-readable breaking change descriptions.
    """
    forward_compatible: bool
    backward_compatible: bool
    breaking_changes: tuple[str, ...] = ()


FieldMapping = CanonicalFieldMapping
