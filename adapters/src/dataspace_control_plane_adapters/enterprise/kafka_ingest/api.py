"""Public import surface for the Kafka ingest adapter."""
from __future__ import annotations

from .config import KafkaSettings
from .consumer import KafkaConsumer
from .dead_letter import DeadLetterProducer
from .errors import KafkaAdapterError, KafkaConsumerError, KafkaProducerError, KafkaSerdeError
from .health import KafkaHealthProbe
from .ports_impl import KafkaIngestPort
from .producer import KafkaProducer

__all__ = [
    "KafkaSettings",
    "KafkaConsumer",
    "KafkaProducer",
    "DeadLetterProducer",
    "KafkaIngestPort",
    "KafkaHealthProbe",
    "KafkaAdapterError",
    "KafkaConsumerError",
    "KafkaProducerError",
    "KafkaSerdeError",
]
