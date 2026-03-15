"""Aggregate roots for the schema_mapping domain."""
from __future__ import annotations
from dataclasses import dataclass, field

from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId
from .enums import MappingDirection, MappingStatus
from .value_objects import MappingRule


@dataclass
class SchemaMapping(AggregateRoot):
    """
    Aggregate representing a versioned, directional mapping between two schemas.
    Rules can be added or removed; each mutation bumps the version counter.
    """
    source_schema_id: str = ""
    target_schema_id: str = ""
    direction: MappingDirection = MappingDirection.INBOUND
    rules: list[MappingRule] = field(default_factory=list)
    status: MappingStatus = MappingStatus.DRAFT
    version: int = 1

    def activate(self) -> None:
        """Transition status to ACTIVE."""
        self.status = MappingStatus.ACTIVE

    def deprecate(self) -> None:
        """Transition status to DEPRECATED."""
        self.status = MappingStatus.DEPRECATED

    def add_rule(self, rule: MappingRule) -> None:
        """Append a new rule and bump the version counter."""
        self.rules.append(rule)
        self.version += 1

    def remove_rule(self, source_path: str) -> None:
        """
        Remove the rule matching source_path and bump the version counter.
        No-op (no error) if the source_path is not present.
        """
        self.rules = [r for r in self.rules if r.source_path != source_path]
        self.version += 1


SchemaMappingSpec = SchemaMapping


@dataclass(frozen=True)
class MappingRevision:
    mapping_id: str
    revision: int


@dataclass(frozen=True)
class SourceSchema:
    schema_id: str
    system_name: str


@dataclass(frozen=True)
class TargetSemanticModel:
    model_id: str
    namespace: str


@dataclass(frozen=True)
class TransformationPipeline:
    steps: tuple[str, ...] = ()


@dataclass(frozen=True)
class LineageGraph:
    edges: tuple[str, ...] = ()


@dataclass(frozen=True)
class MappingApproval:
    approved: bool
    approved_by: str = ""


@dataclass(frozen=True)
class SuggestionRecord:
    suggestion_id: str
    confidence: float
    explanation: str = ""
