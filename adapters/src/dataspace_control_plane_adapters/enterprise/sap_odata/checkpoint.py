"""Watermark/checkpoint state for OData incremental extraction."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass
class ODataCheckpoint:
    """Persistent checkpoint for OData incremental extraction.

    ``last_value`` is an ISO-8601 datetime string or numeric string that matches
    the watermark field type used in ``$filter`` expressions.
    """

    entity_set: str
    watermark_field: str
    last_value: str  # ISO8601 datetime or numeric string
    extracted_at: str  # ISO8601 datetime of when this checkpoint was recorded


def serialize_checkpoint(cp: ODataCheckpoint) -> str:
    """Serialize an ODataCheckpoint to a JSON string for durable storage."""
    return json.dumps(asdict(cp))


def deserialize_checkpoint(s: str) -> ODataCheckpoint:
    """Deserialize an ODataCheckpoint from a JSON string.

    Raises ValueError if the JSON is missing required fields.
    """
    data = json.loads(s)
    return ODataCheckpoint(
        entity_set=data["entity_set"],
        watermark_field=data["watermark_field"],
        last_value=data["last_value"],
        extracted_at=data["extracted_at"],
    )
