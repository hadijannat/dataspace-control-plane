"""Pagination helpers for REST APIs that use cursor, offset, or link-based paging.

EDC management API uses offset+limit; BaSyx uses cursor-based paging;
OData uses `$skiptoken` / `@odata.nextLink`. Each style is handled here.
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Callable, Awaitable


async def paginate_offset(
    fetch: Callable[[int, int], Awaitable[list[Any]]],
    *,
    page_size: int = 100,
    max_pages: int = 10_000,
) -> AsyncIterator[Any]:
    """Iterate over an offset/limit paginated endpoint, yielding individual items."""
    offset = 0
    for _ in range(max_pages):
        page = await fetch(offset, page_size)
        if not page:
            return
        for item in page:
            yield item
        if len(page) < page_size:
            return
        offset += page_size


async def paginate_cursor(
    fetch: Callable[[str | None], Awaitable[tuple[list[Any], str | None]]],
    *,
    max_pages: int = 10_000,
) -> AsyncIterator[Any]:
    """Iterate over a cursor-based paginated endpoint.

    `fetch(cursor)` must return (items, next_cursor_or_None).
    """
    cursor: str | None = None
    for _ in range(max_pages):
        items, next_cursor = await fetch(cursor)
        for item in items:
            yield item
        if next_cursor is None:
            return
        cursor = next_cursor


async def paginate_odata_nextlink(
    fetch: Callable[[str | None], Awaitable[dict[str, Any]]],
    items_key: str = "value",
    nextlink_key: str = "@odata.nextLink",
    *,
    max_pages: int = 10_000,
) -> AsyncIterator[Any]:
    """Iterate over an OData `@odata.nextLink`-based paged response."""
    url: str | None = None
    for _ in range(max_pages):
        response = await fetch(url)
        for item in response.get(items_key, []):
            yield item
        url = response.get(nextlink_key)
        if not url:
            return
