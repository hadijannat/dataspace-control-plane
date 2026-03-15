"""Schema introspection for the SQL extract adapter.

Queries information_schema to discover table column names and types without
requiring pre-declared models. Used to dynamically build extraction queries.
"""
from __future__ import annotations

import logging
from typing import Any

from .config import SqlExtractSettings
from .errors import SqlIntrospectionError

logger = logging.getLogger(__name__)


async def introspect_table(
    settings: SqlExtractSettings, table: str
) -> list[dict[str, str]]:
    """Return column metadata for ``table`` in the configured schema.

    Each returned dict has keys: ``column_name``, ``data_type``,
    ``is_nullable``, ``column_default``.

    Args:
        settings: SqlExtractSettings with schema and DSN.
        table: Unqualified table name.

    Returns:
        List of column metadata dicts ordered by ordinal_position.

    Raises:
        SqlIntrospectionError: If the query fails or the table is not found.
    """
    try:
        import asyncpg  # type: ignore[import]
    except ImportError as exc:
        raise SqlIntrospectionError(
            "asyncpg is not installed. Install it with: pip install asyncpg"
        ) from exc

    try:
        conn = await asyncpg.connect(settings.dsn)
        try:
            rows = await conn.fetch(
                """
                SELECT
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = $1
                  AND table_name   = $2
                ORDER BY ordinal_position
                """,
                settings.source_schema,
                table,
            )
        finally:
            await conn.close()
    except SqlIntrospectionError:
        raise
    except Exception as exc:
        raise SqlIntrospectionError(
            f"Failed to introspect {settings.source_schema}.{table}: {exc}"
        ) from exc

    if not rows:
        raise SqlIntrospectionError(
            f"Table {settings.source_schema}.{table!r} not found or has no columns."
        )

    return [
        {
            "column_name": r["column_name"],
            "data_type": r["data_type"],
            "is_nullable": r["is_nullable"],
            "column_default": r["column_default"],
        }
        for r in rows
    ]


async def list_tables(settings: SqlExtractSettings) -> list[str]:
    """Return all user table names in the configured schema.

    Raises:
        SqlIntrospectionError: If the query fails.
    """
    try:
        import asyncpg  # type: ignore[import]
    except ImportError as exc:
        raise SqlIntrospectionError("asyncpg is not installed.") from exc

    try:
        conn = await asyncpg.connect(settings.dsn)
        try:
            rows = await conn.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = $1
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """,
                settings.source_schema,
            )
        finally:
            await conn.close()
    except SqlIntrospectionError:
        raise
    except Exception as exc:
        raise SqlIntrospectionError(
            f"Failed to list tables in schema {settings.source_schema!r}: {exc}"
        ) from exc

    return [r["table_name"] for r in rows]
