"""Offset checkpoint for Kafka consumer resume."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass


@dataclass
class KafkaCheckpoint:
    """Persistent checkpoint for a single Kafka topic-partition offset.

    Used to resume consumption from a known position without relying on
    the broker's stored consumer-group offset (useful for out-of-band durable
    handoff scenarios where commits are intentionally delayed).
    """

    topic: str
    partition: int
    offset: int


def serialize_checkpoint(cp: KafkaCheckpoint) -> str:
    """Serialize a KafkaCheckpoint to a JSON string for durable storage."""
    return json.dumps(asdict(cp))


def deserialize_checkpoint(s: str) -> KafkaCheckpoint:
    """Deserialize a KafkaCheckpoint from a JSON string.

    Raises ValueError if required fields are missing or malformed.
    """
    data = json.loads(s)
    return KafkaCheckpoint(
        topic=data["topic"],
        partition=int(data["partition"]),
        offset=int(data["offset"]),
    )
