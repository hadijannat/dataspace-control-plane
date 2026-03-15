"""Enumerations for the schema_mapping domain."""
from enum import Enum


class MappingDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"
    BIDIRECTIONAL = "bidirectional"


class TransformType(str, Enum):
    IDENTITY = "identity"
    RENAME = "rename"
    TYPE_CAST = "type_cast"
    ENUM_MAP = "enum_map"
    JSONPATH = "jsonpath"
    CUSTOM = "custom"


class MappingStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
