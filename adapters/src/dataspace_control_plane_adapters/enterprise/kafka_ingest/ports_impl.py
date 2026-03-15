"""Kafka ingest adapter port implementations.

Implements event ingestion port: subscribe to topics, consume messages,
route to dead-letter on failure, checkpoint offsets for resume.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from .checkpoint import KafkaCheckpoint, deserialize_checkpoint, serialize_checkpoint
from .config import KafkaSettings
from .consumer import KafkaConsumer
from .dead_letter import DeadLetterProducer
from .errors import KafkaAdapterError, KafkaConsumerError, KafkaSerdeError
from .serde import decode_envelope

logger = logging.getLogger(__name__)


class KafkaIngestPort:
    """Ingests events from Kafka topics into canonical dicts.

    Responsibilities:
    - Subscribe to one or more topics.
    - Deserialize envelopes via serde module.
    - Forward unparseable messages to the DLQ topic.
    - Provide checkpointing for durable offset tracking.
    - Commit offsets only after the caller confirms durable handoff.
    """

    def __init__(self, settings: KafkaSettings) -> None:
        self._settings = settings
        self._consumer = KafkaConsumer(settings)
        self._dlq = DeadLetterProducer(settings)

    async def start(self, topics: list[str]) -> None:
        """Subscribe to topics and initialize the DLQ producer."""
        await self._consumer.start(topics)
        await self._dlq.start()

    async def poll_event(self, timeout_s: float = 1.0) -> dict[str, Any] | None:
        """Poll for one event and return its canonical payload dict.

        Messages that fail deserialization are routed to the DLQ and None
        is returned so the caller can continue without blocking.

        Returns:
            Canonical event dict (``type``, ``source``, ``payload``, ``metadata``),
            or None if no message arrived within timeout.
        """
        raw = await self._consumer.poll(timeout_s=timeout_s)
        if raw is None:
            return None

        try:
            envelope = decode_envelope(raw["value_bytes"] or b"")
        except KafkaSerdeError as exc:
            logger.warning(
                "Deserialization failed for %s[%d]@%d — routing to DLQ: %s",
                raw["topic"],
                raw["partition"],
                raw["offset"],
                exc,
            )
            try:
                await self._dlq.send_to_dlq(
                    source_topic=raw["topic"],
                    message=raw,
                    reason=str(exc),
                )
            except KafkaAdapterError:
                logger.exception("DLQ delivery also failed — message silently dropped.")
            return None

        return {
            "type": envelope.get("type", "unknown"),
            "source": raw["topic"],
            "key": raw["key"],
            "partition": raw["partition"],
            "offset": raw["offset"],
            "timestamp": raw["timestamp"],
            "headers": raw["headers"],
            "payload": envelope.get("data") or envelope,
        }

    async def commit(self) -> None:
        """Commit the current consumer position.

        Call this only after the polled event has been durably handed off
        (e.g. written to the outbox, confirmed by a Temporal activity).
        """
        await self._consumer.commit()

    def current_checkpoint(self, topic: str, partition: int, offset: int) -> KafkaCheckpoint:
        """Return a checkpoint for the given topic-partition-offset."""
        return KafkaCheckpoint(topic=topic, partition=partition, offset=offset)

    def serialize_checkpoint(self, cp: KafkaCheckpoint) -> str:
        """Serialize a checkpoint to a JSON string for durable storage."""
        return serialize_checkpoint(cp)

    def deserialize_checkpoint(self, s: str) -> KafkaCheckpoint:
        """Restore a checkpoint from a JSON string."""
        return deserialize_checkpoint(s)

    async def close(self) -> None:
        """Shut down consumer and DLQ producer."""
        await self._consumer.close()
        await self._dlq.close()
