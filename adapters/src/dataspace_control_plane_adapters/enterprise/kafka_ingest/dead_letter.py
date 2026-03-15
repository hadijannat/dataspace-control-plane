"""Dead-letter queue (DLQ) producer for the Kafka ingest adapter.

Messages that fail deserialization or processing are forwarded to a
dedicated DLQ topic so that they can be inspected and replayed without
blocking the main consumer loop.

DLQ topic naming convention: ``<source_topic>.dlq``
"""
from __future__ import annotations

import logging
from typing import Any

from .config import KafkaSettings
from .errors import KafkaProducerError

logger = logging.getLogger(__name__)


class DeadLetterProducer:
    """Produces failed messages to a dead-letter topic.

    The DLQ topic name is derived from the source topic by appending ``.dlq``.
    Original message headers, key, and value are preserved; the failure reason
    is injected as the ``x-dlq-reason`` header.

    Uses the same idempotence config as the main producer — even DLQ delivery
    must not duplicate messages.
    """

    def __init__(self, settings: KafkaSettings) -> None:
        self._settings = settings
        self._producer: Any = None  # confluent_kafka.Producer

    def _build_config(self) -> dict[str, Any]:
        cfg: dict[str, Any] = {
            "bootstrap.servers": self._settings.bootstrap_servers,
            "security.protocol": self._settings.security_protocol,
            "acks": self._settings.producer_acks,
            "enable.idempotence": self._settings.producer_enable_idempotence,
            "max.in.flight.requests.per.connection": self._settings.producer_max_in_flight,
            "retries": self._settings.producer_retries,
        }
        if self._settings.sasl_mechanism:
            cfg["sasl.mechanism"] = self._settings.sasl_mechanism
        if self._settings.sasl_username:
            cfg["sasl.username"] = self._settings.sasl_username
        if self._settings.sasl_password:
            cfg["sasl.password"] = self._settings.sasl_password.get_secret_value()
        if self._settings.ssl_ca_location:
            cfg["ssl.ca.location"] = self._settings.ssl_ca_location
        return cfg

    async def start(self) -> None:
        """Initialize the underlying confluent_kafka.Producer."""
        try:
            from confluent_kafka import Producer as _Producer  # type: ignore[import]

            self._producer = _Producer(self._build_config())
        except ImportError as exc:
            raise KafkaProducerError(
                "confluent_kafka is not installed. "
                "Install it with: pip install confluent-kafka"
            ) from exc
        except Exception as exc:
            raise KafkaProducerError(
                f"Failed to initialize DLQ producer: {exc}"
            ) from exc

    async def send_to_dlq(
        self,
        *,
        source_topic: str,
        message: dict[str, Any],
        reason: str,
    ) -> None:
        """Produce a failed message to the dead-letter topic.

        Args:
            source_topic: The original Kafka topic the message came from.
            message: Normalized message dict as returned by KafkaConsumer.poll().
            reason: Human-readable failure reason injected as x-dlq-reason header.

        Raises:
            KafkaProducerError: If delivery fails.
        """
        if self._producer is None:
            raise KafkaProducerError("DLQ producer not started. Call start() first.")

        dlq_topic = f"{source_topic}.dlq"
        headers = dict(message.get("headers") or {})
        headers["x-dlq-reason"] = reason
        headers["x-dlq-source-topic"] = source_topic
        headers["x-dlq-source-partition"] = str(message.get("partition", -1))
        headers["x-dlq-source-offset"] = str(message.get("offset", -1))

        header_list = [(k, v.encode("utf-8") if isinstance(v, str) else v) for k, v in headers.items()]
        key = message.get("key")
        value = message.get("value_bytes")

        try:
            self._producer.produce(
                dlq_topic,
                key=key.encode("utf-8") if isinstance(key, str) else key,
                value=value,
                headers=header_list,
                on_delivery=self._on_delivery,
            )
            self._producer.flush(timeout=10.0)
        except Exception as exc:
            raise KafkaProducerError(
                f"Failed to deliver message to DLQ topic {dlq_topic!r}: {exc}"
            ) from exc

    @staticmethod
    def _on_delivery(err: Any, msg: Any) -> None:
        if err is not None:
            logger.error("DLQ delivery failed: %s", err)

    async def close(self) -> None:
        """Flush and close the DLQ producer."""
        if self._producer is not None:
            try:
                self._producer.flush(timeout=10.0)
            except Exception:
                pass
            finally:
                self._producer = None
