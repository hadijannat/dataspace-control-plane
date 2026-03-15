"""Public import surface for the Kafka ingest adapter."""
from __future__ import annotations

from .checkpoint import KafkaCheckpoint, deserialize_checkpoint, serialize_checkpoint
from .config import KafkaSettings
from .consumer import KafkaConsumer
from .dead_letter import DeadLetterProducer
from .errors import KafkaAdapterError, KafkaConsumerError, KafkaProducerError, KafkaSerdeError
from .ports_impl import KafkaIngestPort
from .producer import KafkaProducer
from .serde import build_envelope, decode_envelope, encode_envelope

__all__ = [
    "KafkaSettings",
    "KafkaConsumer",
    "KafkaProducer",
    "DeadLetterProducer",
    "KafkaIngestPort",
    "KafkaCheckpoint",
    "serialize_checkpoint",
    "deserialize_checkpoint",
    "build_envelope",
    "encode_envelope",
    "decode_envelope",
    "KafkaAdapterError",
    "KafkaConsumerError",
    "KafkaProducerError",
    "KafkaSerdeError",
]
