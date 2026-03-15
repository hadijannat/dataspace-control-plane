"""Full-table snapshot extraction for the SQL extract adapter.

Reads an entire table in memory-bounded chunks using cursor-based pagination
(keyset pagination on the primary key or watermark column). Each chunk is
yielded as a list of canonical row dicts.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from .config import SqlExtractSettings
from .errors import SqlSnapshotError
from .introspection import introspect_table
from .type_mapping import coerce_value

logger = logging.getLogger(__name__)


async def snapshot_table(
    settings: SqlExtractSettings,
    table: str,
    *,
    pk_column: str = "id",
) -> AsyncIterator[list[dict[str, Any]]]:
    """Yield chunks of rows from a full-table snapshot.

    Uses keyset pagination on ``pk_column`` to avoid OFFSET-based performance
    degradation on large tables.

    Args:
        settings: SqlExtractSettings.
        table: Unqualified table name.
        pk_column: Primary key column used for keyset pagination cursor.

    Yields:
        List of canonical row dicts (up to ``settings.snapshot_chunk_size`` each).

    Raises:
        SqlSnapshotError: If any query fails.
    """
    try:
        import asyncpg  # type: ignore[import]
    except ImportError as exc:
        raise SqlSnapshotError("asyncpg is not installed.") from exc

    try:
        columns = await introspect_table(settings, table)
    except Exception as exc:
        raise SqlSnapshotError(
            f"Cannot snapshot {table}: introspection failed: {exc}"
        ) from exc

    col_type_map = {c["column_name"]: c["data_type"] for c in columns}
    qualified = f"{settings.source_schema}.{table}"
    chunk_size = settings.snapshot_chunk_size
    cursor_value: Any = None

    conn = None
    try:
        import asyncpg  # type: ignore[import]

        conn = await asyncpg.connect(settings.dsn)
        while True:
            if cursor_value is None:
                query = (
                    f"SELECT * FROM {qualified} "
                    f"ORDER BY {pk_column} ASC LIMIT {chunk_size}"
                )
                rows = await conn.fetch(query)
            else:
                query = (
                    f"SELECT * FROM {qualified} "
                    f"WHERE {pk_column} > $1 "
                    f"ORDER BY {pk_column} ASC LIMIT {chunk_size}"
                )
                rows = await conn.fetch(query, cursor_value)

            if not rows:
                break

            chunk = []
            for row in rows:
                canonical = {
                    col: coerce_value(row[col], col_type_map.get(col, "text"))
                    for col in row.keys()
                }
                chunk.append(canonical)

            cursor_value = rows[-1][pk_column]
            yield chunk

            if len(rows) < chunk_size:
                break

    except SqlSnapshotError:
        raise
    except Exception as exc:
        raise SqlSnapshotError(
            f"Snapshot extraction failed for {qualified}: {exc}"
        ) from exc
    finally:
        if conn is not None:
            await conn.close()
