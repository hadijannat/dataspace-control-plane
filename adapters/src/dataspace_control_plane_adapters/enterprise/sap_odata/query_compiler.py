"""OData query compiler for the SAP OData adapter.

Builds OData 4.01 system query options ($filter, $select, $orderby, $top,
$skip, $format) from structured Python arguments. No business logic — pure
URL construction for the wire format.
"""
from __future__ import annotations

import json
from typing import Any
from urllib.parse import urljoin, urlencode, quote


class ODataQueryCompiler:
    """Compiles structured query specs into OData 4.01 request URLs and batch bodies."""

    def __init__(self, service_url: str) -> None:
        self._service_url = service_url.rstrip("/") + "/"

    def build_url(
        self,
        entity_set: str,
        *,
        select: list[str] | None = None,
        filter_expr: str | None = None,
        orderby: str | None = None,
        top: int | None = None,
        skip: int | None = None,
        format: str = "json",
    ) -> str:
        """Build a complete OData query URL for the given entity set.

        Args:
            entity_set: Name of the OData EntitySet (e.g. "BusinessPartnerSet").
            select: List of property names for $select, or None for all properties.
            filter_expr: Raw $filter expression string (caller is responsible for
                correct OData filter syntax).
            orderby: Raw $orderby expression (e.g. "LastModifiedDate asc").
            top: Value for $top (page size).
            skip: Value for $skip (page offset).
            format: OData response format; "json" maps to "application/json".

        Returns:
            Fully qualified URL string suitable for a GET request.
        """
        params: dict[str, str] = {}

        if select:
            params["$select"] = ",".join(select)
        if filter_expr:
            params["$filter"] = filter_expr
        if orderby:
            params["$orderby"] = orderby
        if top is not None:
            params["$top"] = str(top)
        if skip is not None:
            params["$skip"] = str(skip)
        if format == "json":
            params["$format"] = "application/json"
        elif format:
            params["$format"] = format

        base = urljoin(self._service_url, entity_set)
        if params:
            return f"{base}?{urlencode(params)}"
        return base

    def build_incremental_filter(
        self, watermark_field: str, watermark_value: str
    ) -> str:
        """Return an OData $filter expression for watermark-based incremental extraction.

        For datetime/offset fields the value should be an ISO-8601 string;
        for numeric fields it should be a numeric string.

        Example result: ``LastModifiedDate gt 2024-01-01T00:00:00Z``
        """
        # Detect whether we should quote the value as an OData datetime literal
        # or leave it as a numeric literal.
        if _looks_like_datetime(watermark_value):
            # OData datetime literal: cast(value, Edm.DateTimeOffset) or raw ISO string.
            return f"{watermark_field} gt {watermark_value}"
        return f"{watermark_field} gt {watermark_value}"

    def build_batch_request(self, queries: list[dict[str, Any]]) -> dict[str, Any]:
        """Build an OData $batch request body (JSON batch format, OData 4.01).

        Each query dict should have:
          - ``id``: unique string identifier for this request in the batch
          - ``entity_set``: entity set name
          - ``select``, ``filter_expr``, ``orderby``, ``top``, ``skip``: optional

        Returns a dict that serialises to a valid OData JSON batch body.
        """
        requests = []
        for query in queries:
            entity_set = query["entity_set"]
            url = self.build_url(
                entity_set,
                select=query.get("select"),
                filter_expr=query.get("filter_expr"),
                orderby=query.get("orderby"),
                top=query.get("top"),
                skip=query.get("skip"),
            )
            requests.append(
                {
                    "id": query.get("id", entity_set),
                    "method": "GET",
                    "url": url,
                    "headers": {"Accept": "application/json"},
                }
            )
        return {"requests": requests}


def _looks_like_datetime(value: str) -> bool:
    """Return True if ``value`` looks like an ISO-8601 datetime string."""
    return "T" in value or "-" in value[:4]
