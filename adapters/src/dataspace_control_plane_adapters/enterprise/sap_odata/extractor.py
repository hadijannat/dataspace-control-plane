"""Full-snapshot and incremental OData extractor for the SAP OData adapter."""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

import httpx

from ..._shared.pagination import paginate_odata_nextlink
from .config import SapOdataSettings
from .errors import ODataQueryError
from .metadata_client import ODataMetadataClient
from .query_compiler import ODataQueryCompiler


class SapOdataExtractor:
    """Extracts records from an OData 4.01 service via full-snapshot or incremental mode.

    All yielded records include envelope fields:
      ``__source``, ``__entity_set``, ``__tenant_id``

    Pagination follows ``@odata.nextLink`` automatically.
    """

    def __init__(
        self,
        settings: SapOdataSettings,
        tenant_id: str,
        metadata_client: ODataMetadataClient | None = None,
    ) -> None:
        self._settings = settings
        self._tenant_id = tenant_id
        self._metadata_client = metadata_client or ODataMetadataClient(settings)
        self._compiler = ODataQueryCompiler(str(settings.service_url))
        self._auth = (
            settings.username,
            settings.password.get_secret_value(),
        )

    async def extract_snapshot(
        self,
        entity_set: str,
        *,
        select: list[str] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield all records for an entity set using OData pagination.

        Follows ``@odata.nextLink`` until exhausted. Each record is enriched
        with source-envelope metadata fields.
        """
        await self._metadata_client.ensure_fresh()

        # Build first-page URL using configured page_size.
        first_url = self._compiler.build_url(
            entity_set,
            select=select,
            top=self._settings.page_size,
            skip=0,
        )

        async def _fetch_page(url: str | None) -> dict[str, Any]:
            target = url if url is not None else first_url
            return await self._get_json(target)

        async for record in paginate_odata_nextlink(_fetch_page):
            yield self._enrich(record, entity_set)

    async def extract_incremental(
        self,
        entity_set: str,
        watermark_field: str,
        since: str,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield records newer than ``since`` using a watermark $filter.

        The watermark $filter is ``{watermark_field} gt {since}``.
        Pagination follows ``@odata.nextLink`` until exhausted.
        """
        await self._metadata_client.ensure_fresh()

        filter_expr = self._compiler.build_incremental_filter(watermark_field, since)
        first_url = self._compiler.build_url(
            entity_set,
            filter_expr=filter_expr,
            orderby=f"{watermark_field} asc",
            top=self._settings.page_size,
            skip=0,
        )

        async def _fetch_page(url: str | None) -> dict[str, Any]:
            target = url if url is not None else first_url
            return await self._get_json(target)

        async for record in paginate_odata_nextlink(_fetch_page):
            yield self._enrich(record, entity_set)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _get_json(self, url: str) -> dict[str, Any]:
        """Execute a GET request and return the parsed JSON body."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(
                    url,
                    auth=self._auth,
                    headers={"Accept": "application/json"},
                )
                resp.raise_for_status()
                return resp.json()  # type: ignore[return-value]
        except httpx.HTTPStatusError as exc:
            raise ODataQueryError(
                f"OData request failed ({exc.response.status_code}): {url}",
                upstream_code=exc.response.status_code,
            ) from exc
        except Exception as exc:
            raise ODataQueryError(f"OData request error for {url}: {exc}") from exc

    def _enrich(self, record: dict[str, Any], entity_set: str) -> dict[str, Any]:
        """Add source-envelope fields to a raw OData record."""
        return {
            "__source": "sap_odata",
            "__entity_set": entity_set,
            "__tenant_id": self._tenant_id,
            **record,
        }
