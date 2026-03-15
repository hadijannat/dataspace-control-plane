"""PostgreSQL adapter-specific error hierarchy.

Rules:
- PostgresError is the root of all Postgres-layer exceptions.
- PostgresTenancyViolation is raised when a query escapes the expected tenant context.
- PostgresVersionConflict is raised on optimistic-concurrency mismatch (version mismatch).
- All callers translate these into core-layer errors at the service boundary.
"""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.errors import (
    AdapterError,
    AdapterConflictError,
    AdapterNotFoundError,
)


class PostgresError(AdapterError):
    """Root for all PostgreSQL adapter errors."""


class PostgresTenancyViolation(PostgresError):
    """Raised when a query attempts to access rows outside the active tenant context.

    This indicates a programming error — tenant context must be set before any query.
    """


class PostgresVersionConflict(AdapterConflictError):
    """Raised when an aggregate's expected_version does not match the stored version.

    Callers should reload the aggregate and retry the command.
    """

    def __init__(self, aggregate_id: str, expected: int, actual: int) -> None:
        super().__init__(
            f"Version conflict for aggregate {aggregate_id!r}: "
            f"expected {expected}, found {actual}",
            upstream_code="version_conflict",
        )
        self.aggregate_id = aggregate_id
        self.expected = expected
        self.actual = actual


class PostgresRecordNotFound(AdapterNotFoundError):
    """Raised when a row is expected but not found in Postgres."""

    def __init__(self, table: str, id_value: str) -> None:
        super().__init__(f"Row not found in {table!r} with id={id_value!r}")
        self.table = table
        self.id_value = id_value
