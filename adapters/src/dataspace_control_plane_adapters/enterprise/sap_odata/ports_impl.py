"""SchemaRegistryPort implementation backed by OData $metadata for the SAP OData adapter."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .config import SapOdataSettings
from .metadata_client import ODataMetadataClient


class SapOdataSchemaRegistryAdapter:
    """Derives and caches JSON schemas from OData $metadata entity types.

    Satisfies the SchemaRegistryPort contract from core/schema_mapping/ports.py.
    Schema IDs are deterministic SHA-256 digests of (tenant_id, entity_set, schema_json)
    so that repeated registrations of unchanged schemas are idempotent.
    """

    def __init__(self, settings: SapOdataSettings) -> None:
        self._settings = settings
        self._metadata_client = ODataMetadataClient(settings)
        # In-memory store: (tenant_id, schema_id) → schema dict.
        # In production wire to a durable registry via core ports.
        self._store: dict[tuple[str, str], dict[str, Any]] = {}

    async def register(self, tenant_id: str, schema: dict[str, Any]) -> str:
        """Register a schema derived from OData metadata and return its schema ID.

        The schema dict is expected to have an ``entity_set`` key identifying
        which EntitySet to derive the JSON Schema for. If ``entity_set`` is not
        present, the provided schema is stored as-is.
        """
        await self._metadata_client.ensure_fresh()

        entity_set = schema.get("entity_set")
        if entity_set:
            derived = self._derive_json_schema(entity_set)
            merged = {**derived, **schema}
        else:
            merged = dict(schema)

        schema_id = _schema_id(tenant_id, merged)
        self._store[(tenant_id, schema_id)] = merged
        return schema_id

    async def get(self, tenant_id: str, schema_id: str) -> dict[str, Any]:
        """Retrieve a previously registered schema.

        Raises KeyError if not found; callers should translate to the appropriate
        domain error at the procedure boundary.
        """
        key = (tenant_id, schema_id)
        if key not in self._store:
            raise KeyError(f"Schema '{schema_id}' not found for tenant '{tenant_id}'.")
        return dict(self._store[key])

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _derive_json_schema(self, entity_set: str) -> dict[str, Any]:
        """Derive a JSON Schema draft-07 document from OData $metadata properties."""
        properties = self._metadata_client.get_entity_type(entity_set)
        json_properties: dict[str, Any] = {}
        required: list[str] = []

        for prop_name, prop_def in properties.items():
            edm_type = prop_def.get("type", "Edm.String")
            json_type = _edm_to_json_schema_type(edm_type)
            json_properties[prop_name] = json_type
            if not prop_def.get("nullable", True):
                required.append(prop_name)

        schema: dict[str, Any] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": entity_set,
            "properties": json_properties,
        }
        if required:
            schema["required"] = required
        return schema


def _edm_to_json_schema_type(edm_type: str) -> dict[str, Any]:
    """Map an OData EDM primitive type to a JSON Schema type definition."""
    mapping: dict[str, dict[str, Any]] = {
        "Edm.String": {"type": "string"},
        "Edm.Int16": {"type": "integer"},
        "Edm.Int32": {"type": "integer"},
        "Edm.Int64": {"type": "integer"},
        "Edm.Decimal": {"type": "number"},
        "Edm.Single": {"type": "number"},
        "Edm.Double": {"type": "number"},
        "Edm.Boolean": {"type": "boolean"},
        "Edm.DateTime": {"type": "string", "format": "date-time"},
        "Edm.DateTimeOffset": {"type": "string", "format": "date-time"},
        "Edm.Date": {"type": "string", "format": "date"},
        "Edm.Guid": {"type": "string", "format": "uuid"},
        "Edm.Binary": {"type": "string", "contentEncoding": "base64"},
    }
    return mapping.get(edm_type, {"type": "string"})


def _schema_id(tenant_id: str, schema: dict[str, Any]) -> str:
    """Produce a deterministic schema ID from tenant + schema content."""
    payload = json.dumps({"tenant_id": tenant_id, "schema": schema}, sort_keys=True)
    return "odata:" + hashlib.sha256(payload.encode()).hexdigest()[:32]
