"""Error types for the SQL extract adapter."""
from __future__ import annotations

from ..._shared.errors import AdapterError, AdapterValidationError


class SqlExtractError(AdapterError):
    """Root error for the SQL extract adapter."""


class SqlIntrospectionError(SqlExtractError):
    """Failed to introspect the source schema (information_schema query failed)."""


class SqlSnapshotError(SqlExtractError):
    """Failed to execute a full-table snapshot query."""


class SqlWatermarkError(SqlExtractError):
    """Failed to read or advance the watermark for incremental extraction."""


class SqlCdcError(SqlExtractError):
    """Failed to consume CDC events from the logical replication stream."""


class SqlTypeMapError(AdapterValidationError):
    """Cannot map a source SQL type to a canonical Python/JSON type."""
