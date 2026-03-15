"""Domain errors for the schema_mapping domain."""
from __future__ import annotations

from dataspace_control_plane_core.domains._shared.errors import (
    DomainError,
    NotFoundError,
    ConflictError,
)


class MappingNotFoundError(NotFoundError):
    """Raised when a SchemaMapping cannot be located by ID."""


class DuplicateMappingError(ConflictError):
    """Raised when a mapping for the same source/target schema pair already exists."""


class InactiveMappingError(DomainError):
    """Raised when an operation requires an ACTIVE mapping but it is not active."""


class DuplicateRuleError(DomainError):
    """Raised when adding a rule whose source_path already exists in the mapping."""
