"""OData $metadata fetcher and in-memory cache for the SAP OData adapter."""
from __future__ import annotations

import time
from typing import Any
from urllib.parse import urljoin

import httpx

from .config import SapOdataSettings
from .errors import ODataMetadataError


class ODataMetadataClient:
    """Fetches and caches OData $metadata for a single service endpoint.

    The metadata document is parsed from the JSON representation
    (Accept: application/json) and cached in memory for ``metadata_cache_ttl_s``
    seconds. Callers should call ``ensure_fresh()`` before querying entity types.
    """

    def __init__(self, settings: SapOdataSettings) -> None:
        self._settings = settings
        self._cache: dict[str, Any] | None = None
        self._fetched_at: float = 0.0

    def is_stale(self) -> bool:
        """Return True if the cache is empty or past TTL."""
        if self._cache is None:
            return True
        age = time.monotonic() - self._fetched_at
        return age > self._settings.metadata_cache_ttl_s

    async def fetch(self) -> dict[str, Any]:
        """Fetch $metadata from the OData service and cache the result.

        Uses HTTP Basic auth and requests JSON format via Accept header.
        Raises ODataMetadataError on HTTP or parse failures.
        """
        url = urljoin(str(self._settings.service_url), "$metadata")
        auth = (
            self._settings.username,
            self._settings.password.get_secret_value(),
        )
        headers = {"Accept": "application/json"}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, auth=auth, headers=headers)
                resp.raise_for_status()
                data: dict[str, Any] = resp.json()
        except httpx.HTTPStatusError as exc:
            raise ODataMetadataError(
                f"HTTP {exc.response.status_code} fetching $metadata from {url}",
                upstream_code=exc.response.status_code,
            ) from exc
        except Exception as exc:
            raise ODataMetadataError(
                f"Failed to fetch $metadata from {url}: {exc}"
            ) from exc

        self._cache = data
        self._fetched_at = time.monotonic()
        return data

    async def ensure_fresh(self) -> None:
        """Re-fetch $metadata if the cache is stale."""
        if self.is_stale():
            await self.fetch()

    def get_entity_type(self, entity_set_name: str) -> dict[str, Any]:
        """Return the property definitions for a named entity set.

        Navigates the cached metadata document to find the EntityType that
        backs the requested EntitySet. Returns a dict of property name →
        ``{"type": "Edm.XXX", "nullable": bool}``.

        Raises ODataMetadataError if the cache is empty or entity set is not found.
        """
        if self._cache is None:
            raise ODataMetadataError(
                "Metadata cache is empty; call ensure_fresh() first."
            )

        # Standard JSON $metadata layout:
        # {"$Version": "4.0", "<Namespace>": {"<EntityType>": {...}, ...}}
        schema_ns = self._find_schema_namespace()
        entity_sets = self._collect_entity_sets(schema_ns)
        entity_type_name = entity_sets.get(entity_set_name)
        if entity_type_name is None:
            raise ODataMetadataError(
                f"EntitySet '{entity_set_name}' not found in $metadata."
            )

        # Strip namespace prefix if present (e.g. "Namespace.TypeName" → "TypeName")
        simple_name = entity_type_name.split(".")[-1]
        entity_type_def = schema_ns.get(simple_name)
        if entity_type_def is None:
            raise ODataMetadataError(
                f"EntityType '{simple_name}' not found in $metadata schema."
            )

        properties: dict[str, Any] = {}
        for prop_name, prop_def in entity_type_def.items():
            if prop_name.startswith("$") or prop_name == "$Key":
                continue
            if isinstance(prop_def, dict):
                properties[prop_name] = {
                    "type": prop_def.get("$Type", "Edm.String"),
                    "nullable": prop_def.get("$Nullable", True),
                    "max_length": prop_def.get("$MaxLength"),
                }
        return properties

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _find_schema_namespace(self) -> dict[str, Any]:
        """Return the first non-metadata top-level namespace dict."""
        assert self._cache is not None
        for key, value in self._cache.items():
            if not key.startswith("$") and isinstance(value, dict):
                return value
        raise ODataMetadataError(
            "Could not locate a schema namespace in the $metadata document."
        )

    def _collect_entity_sets(self, schema_ns: dict[str, Any]) -> dict[str, str]:
        """Return a mapping of EntitySet name → EntityType name from the schema."""
        entity_sets: dict[str, str] = {}
        for _type_or_container, definition in schema_ns.items():
            if not isinstance(definition, dict):
                continue
            # EntityContainer holds EntitySet definitions.
            if definition.get("$Kind") == "EntityContainer":
                for es_name, es_def in definition.items():
                    if es_name.startswith("$"):
                        continue
                    if isinstance(es_def, dict) and es_def.get("$Collection") is True:
                        entity_sets[es_name] = es_def.get("$Type", es_name)
        return entity_sets
