"""Watermark management for incremental SQL extraction.

The watermark is the value of the ``watermark_column`` (e.g. ``updated_at``)
from the last successfully extracted batch. It is persisted externally
(by the calling activity) so extraction can resume without re-reading
already-processed rows.
"""
from __future__ import annotations

import logging
from typing import Any

from .config import SqlExtractSettings
from .errors import SqlWatermarkError

logger = logging.getLogger(__name__)


async def read_max_watermark(
    settings: SqlExtractSettings, table: str, current_watermark: Any
) -> tuple[list[dict[str, Any]], Any]:
    """Fetch rows added/updated after ``current_watermark``.

    Queries ``schema.table WHERE watermark_column > $1 ORDER BY watermark_column``
    and returns (rows, new_watermark) where new_watermark is the maximum value
    of the watermark column in the returned batch.

    Args:
        settings: SqlExtractSettings.
        table: Unqualified table name.
        current_watermark: Exclusive lower bound for the watermark column.
            Pass None to fetch all rows (initial load).

    Returns:
        Tuple of (list_of_row_dicts, new_watermark_value). new_watermark is None
        if no rows were returned (extraction is up to date).

    Raises:
        SqlWatermarkError: If the query fails.
    """
    try:
        import asyncpg  # type: ignore[import]
    except ImportError as exc:
        raise SqlWatermarkError("asyncpg is not installed.") from exc

    wm_col = settings.watermark_column
    qualified = f"{settings.source_schema}.{table}"

    try:
        conn = await asyncpg.connect(settings.dsn)
        try:
            if current_watermark is None:
                query = f"SELECT * FROM {qualified} ORDER BY {wm_col} ASC"
                rows = await conn.fetch(query)
            else:
                query = (
                    f"SELECT * FROM {qualified} "
                    f"WHERE {wm_col} > $1 ORDER BY {wm_col} ASC"
                )
                rows = await conn.fetch(query, current_watermark)
        finally:
            await conn.close()
    except SqlWatermarkError:
        raise
    except Exception as exc:
        raise SqlWatermarkError(
            f"Watermark query failed for {qualified}: {exc}"
        ) from exc

    if not rows:
        return [], None

    row_dicts = [dict(r) for r in rows]
    new_wm = row_dicts[-1].get(wm_col)
    return row_dicts, new_wm
