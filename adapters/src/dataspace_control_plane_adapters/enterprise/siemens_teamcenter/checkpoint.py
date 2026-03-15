"""Checkpoint state for Teamcenter incremental extraction."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass
class TeamcenterCheckpoint:
    """Persistent checkpoint for Teamcenter incremental extraction.

    ``last_modified_date`` is an ISO-8601 string used to filter items
    modified after the last successful extraction run.
    ``last_item_id`` records the last successfully processed item ID for
    safe resume within a partial run.
    """

    last_modified_date: str  # ISO8601
    last_item_id: str


def serialize_checkpoint(cp: TeamcenterCheckpoint) -> str:
    """Serialize a TeamcenterCheckpoint to a JSON string for durable storage."""
    return json.dumps(asdict(cp))


def deserialize_checkpoint(s: str) -> TeamcenterCheckpoint:
    """Deserialize a TeamcenterCheckpoint from a JSON string.

    Raises ValueError if required fields are missing.
    """
    data = json.loads(s)
    return TeamcenterCheckpoint(
        last_modified_date=data["last_modified_date"],
        last_item_id=data["last_item_id"],
    )
