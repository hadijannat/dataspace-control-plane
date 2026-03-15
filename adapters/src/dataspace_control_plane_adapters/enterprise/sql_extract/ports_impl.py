"""SQL extract adapter port implementations.

Provides snapshot and incremental extraction from PostgreSQL.
Used by procedures/ activities to ingest relational data into the dataspace.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from .config import SqlExtractSettings
from .errors import SqlExtractError
from .introspection import introspect_table, list_tables
from .snapshot import snapshot_table
from .watermark import read_max_watermark

logger = logging.getLogger(__name__)


class SqlExtractPort:
    """Implements the core SQL extraction port.

    Callers (procedures/ activities) use this to:
    - Snapshot a full table in memory-bounded chunks.
    - Incrementally extract rows added/updated since a watermark.
    - Introspect table schemas for dynamic pipelines.

    CDC is available via ``cdc_postgres.consume_cdc()`` directly for
    callers that need streaming change events.
    """

    def __init__(self, settings: SqlExtractSettings) -> None:
        self._settings = settings

    async def list_tables(self) -> list[str]:
        """Return all user table names in the configured schema."""
        return await list_tables(self._settings)

    async def describe_table(self, table: str) -> list[dict[str, str]]:
        """Return column metadata for ``table``.

        Each dict has: ``column_name``, ``data_type``, ``is_nullable``,
        ``column_default``.
        """
        return await introspect_table(self._settings, table)

    def snapshot(
        self, table: str, *, pk_column: str = "id"
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Async iterator over full-table snapshot chunks.

        Yields lists of canonical row dicts, each up to
        ``settings.snapshot_chunk_size`` rows.

        Args:
            table: Unqualified table name.
            pk_column: Primary key column for keyset pagination.
        """
        return snapshot_table(self._settings, table, pk_column=pk_column)

    async def incremental(
        self, table: str, *, current_watermark: Any = None
    ) -> tuple[list[dict[str, Any]], Any]:
        """Extract rows updated after ``current_watermark``.

        Args:
            table: Unqualified table name.
            current_watermark: Exclusive lower bound on the watermark column.
                Pass None for initial load (returns all rows).

        Returns:
            Tuple of (row_dicts, new_watermark). new_watermark is None
            if no rows were returned.
        """
        return await read_max_watermark(
            self._settings, table, current_watermark
        )
