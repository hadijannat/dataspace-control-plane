"""Kafka message serialization and deserialization for the Kafka ingest adapter.

Envelope contract:
    {
        "schema_id":        str,   # identifies the payload schema version
        "tenant_id":        str,   # owning tenant
        "event_type":       str,   # domain event type name
        "correlation_id":   str,   # trace/correlation identifier
        "source_topic":     str,   # original Kafka topic
        "source_partition": int,   # original Kafka partition
        "source_offset":    int,   # original Kafka offset
        "source_key":       str | None,
        "payload":          dict,  # event-specific payload
    }
"""
from __future__ import annotations

import json
from typing import Any

from .errors import KafkaSerdeError

# Required fields in every envelope.
_REQUIRED_ENVELOPE_FIELDS = frozenset(
    {
        "schema_id",
        "tenant_id",
        "event_type",
        "correlation_id",
        "source_topic",
        "source_partition",
        "source_offset",
        "payload",
    }
)


def build_envelope(
    event_type: str,
    tenant_id: str,
    payload: dict[str, Any],
    source_topic: str,
    partition: int,
    offset: int,
    correlation_id: str,
    *,
    schema_id: str = "v1",
    source_key: str | None = None,
) -> dict[str, Any]:
    """Construct a normalized Kafka message envelope dict.

    Args:
        event_type: Domain event type name (e.g. "asset.created").
        tenant_id: Owning tenant identifier.
        payload: Event-specific data dict.
        source_topic: Kafka topic the message was consumed from.
        partition: Kafka partition number.
        offset: Kafka offset of the source message.
        correlation_id: Trace or correlation identifier for observability.
        schema_id: Schema version identifier; defaults to "v1".
        source_key: Optional Kafka message key from the source message.

    Returns:
        A fully populated envelope dict ready for ``encode_envelope``.
    """
    return {
        "schema_id": schema_id,
        "tenant_id": tenant_id,
        "event_type": event_type,
        "correlation_id": correlation_id,
        "source_topic": source_topic,
        "source_partition": partition,
        "source_offset": offset,
        "source_key": source_key,
        "payload": payload,
    }


def encode_envelope(envelope: dict[str, Any]) -> bytes:
    """JSON-serialize an envelope dict to bytes for Kafka message values.

    Raises KafkaSerdeError on serialization failure.
    """
    try:
        return json.dumps(envelope, default=str).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise KafkaSerdeError(f"Envelope serialization failed: {exc}") from exc


def decode_envelope(data: bytes) -> dict[str, Any]:
    """Deserialize and validate a Kafka message value bytes into an envelope dict.

    Raises KafkaSerdeError on deserialization or schema validation failure.
    """
    try:
        envelope: dict[str, Any] = json.loads(data.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise KafkaSerdeError(f"Envelope deserialization failed: {exc}") from exc

    missing = _REQUIRED_ENVELOPE_FIELDS - envelope.keys()
    if missing:
        raise KafkaSerdeError(
            f"Envelope is missing required fields: {sorted(missing)}"
        )
    return envelope
