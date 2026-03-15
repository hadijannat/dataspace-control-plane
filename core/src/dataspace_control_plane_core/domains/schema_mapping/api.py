"""Public import surface for the schema_mapping domain."""
from .model.enums import MappingDirection, TransformType, MappingStatus
from .model.value_objects import CompatibilityVector, FieldMapping, MappingLineage, MappingRule
from .model.aggregates import (
    LineageGraph,
    MappingApproval,
    MappingRevision,
    SchemaMapping,
    SchemaMappingSpec,
    SourceSchema,
    SuggestionRecord,
    TargetSemanticModel,
    TransformationPipeline,
)
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
from .ports import (
    SchemaMappingRepository,
    SchemaRegistryPort,
    SourceSchemaIntrospectorPort,
    TemplateProviderPort,
    TransformationExecutorPort,
    UnitConversionPort,
)
from .services import SchemaMappingService

__all__ = [
    # enums
    "MappingDirection",
    "TransformType",
    "MappingStatus",
    # value objects
    "MappingRule",
    "FieldMapping",
    "MappingLineage",
    "CompatibilityVector",
    # aggregates
    "SchemaMapping",
    "SchemaMappingSpec",
    "MappingRevision",
    "SourceSchema",
    "TargetSemanticModel",
    "TransformationPipeline",
    "LineageGraph",
    "MappingApproval",
    "SuggestionRecord",
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
    "SourceSchemaIntrospectorPort",
    "TemplateProviderPort",
    "TransformationExecutorPort",
    "UnitConversionPort",
    # services
    "SchemaMappingService",
]
