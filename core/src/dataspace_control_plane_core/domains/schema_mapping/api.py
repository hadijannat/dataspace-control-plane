"""Public import surface for the schema_mapping domain."""
from .model.enums import MappingDirection, TransformType, MappingStatus
from .model.value_objects import MappingRule, MappingLineage, CompatibilityVector
from .model.aggregates import SchemaMapping
from .model.invariants import require_at_least_one_rule, require_no_duplicate_source_paths
from .commands import (
    CreateMappingCommand,
    ActivateMappingCommand,
    AddMappingRuleCommand,
    RemoveMappingRuleCommand,
    DeprecateMappingCommand,
)
from .events import (
    MappingCreated,
    MappingActivated,
    MappingRuleAdded,
    MappingDeprecated,
)
from .errors import (
    MappingNotFoundError,
    DuplicateMappingError,
    InactiveMappingError,
    DuplicateRuleError,
)
from .ports import SchemaMappingRepository, SchemaRegistryPort
from .services import SchemaMappingService

__all__ = [
    # enums
    "MappingDirection",
    "TransformType",
    "MappingStatus",
    # value objects
    "MappingRule",
    "MappingLineage",
    "CompatibilityVector",
    # aggregates
    "SchemaMapping",
    # invariants
    "require_at_least_one_rule",
    "require_no_duplicate_source_paths",
    # commands
    "CreateMappingCommand",
    "ActivateMappingCommand",
    "AddMappingRuleCommand",
    "RemoveMappingRuleCommand",
    "DeprecateMappingCommand",
    # events
    "MappingCreated",
    "MappingActivated",
    "MappingRuleAdded",
    "MappingDeprecated",
    # errors
    "MappingNotFoundError",
    "DuplicateMappingError",
    "InactiveMappingError",
    "DuplicateRuleError",
    # ports
    "SchemaMappingRepository",
    "SchemaRegistryPort",
    # services
    "SchemaMappingService",
]
