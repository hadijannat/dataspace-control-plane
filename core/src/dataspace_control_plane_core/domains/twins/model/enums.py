"""Enumerations for the twins domain."""
from enum import Enum


class TwinVisibility(str, Enum):
    PRIVATE = "private"
    PUBLIC = "public"
    RESTRICTED = "restricted"


class TwinLifecycleState(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"
    WITHDRAWN = "withdrawn"


class SubmodelCategory(str, Enum):
    TECHNICAL_DATA = "technical_data"
    DOCUMENTATION = "documentation"
    CARBON_FOOTPRINT = "carbon_footprint"
    BATTERY_PASSPORT = "battery_passport"
    CUSTOM = "custom"
