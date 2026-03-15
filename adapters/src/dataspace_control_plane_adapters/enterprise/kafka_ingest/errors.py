"""Error types for the Kafka ingest adapter."""
from __future__ import annotations

from ..._shared.errors import AdapterError, AdapterSerdeError


class KafkaAdapterError(AdapterError):
    """Root error for the Kafka ingest adapter."""


class KafkaProducerError(KafkaAdapterError):
    """Failed to produce a message to Kafka."""


class KafkaConsumerError(KafkaAdapterError):
    """Failed to consume messages from Kafka."""


class KafkaSerdeError(AdapterSerdeError):
    """Failed to serialize or deserialize a Kafka message envelope."""
