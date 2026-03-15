"""Kafka consumer wrapper for the Kafka ingest adapter.

Wraps confluent_kafka.Consumer with a normalized message interface.
Commits are deliberately deferred: ``commit()`` must be called by the caller
only after a durable handoff has been confirmed.
"""
from __future__ import annotations

from typing import Any

from .config import KafkaSettings
from .errors import KafkaConsumerError


class KafkaConsumer:
    """Async-style Kafka consumer backed by confluent_kafka.Consumer.

    This wrapper normalises confluent_kafka's synchronous Consumer API into
    an interface compatible with the rest of the async adapter stack. Actual
    I/O is synchronous at the confluent_kafka level; wrap in a thread executor
    for full async compliance if needed in a high-throughput async event loop.

    Commit policy:
        ``commit()`` must be called by the caller explicitly after confirming
        durable handoff of the message. Never auto-commit.
    """

    def __init__(self, settings: KafkaSettings) -> None:
        self._settings = settings
        self._consumer: Any = None  # confluent_kafka.Consumer

    def _build_config(self) -> dict[str, Any]:
        """Build the confluent_kafka consumer configuration dict."""
        cfg: dict[str, Any] = {
            "bootstrap.servers": self._settings.bootstrap_servers,
            "security.protocol": self._settings.security_protocol,
            "group.id": self._settings.consumer_group_id,
            "auto.offset.reset": self._settings.consumer_auto_offset_reset,
            "enable.auto.commit": False,  # Explicit commits only.
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

    async def start(self, topics: list[str]) -> None:
        """Subscribe to the given topics and create the underlying consumer.

        Raises KafkaConsumerError if confluent_kafka is not installed or
        subscription fails.
        """
        try:
            from confluent_kafka import Consumer as _Consumer  # type: ignore[import]

            self._consumer = _Consumer(self._build_config())
            self._consumer.subscribe(topics)
        except ImportError as exc:
            raise KafkaConsumerError(
                "confluent_kafka is not installed. "
                "Install it with: pip install confluent-kafka"
            ) from exc
        except Exception as exc:
            raise KafkaConsumerError(
                f"Failed to start Kafka consumer for topics {topics}: {exc}"
            ) from exc

    async def poll(self, timeout_s: float = 1.0) -> dict[str, Any] | None:
        """Poll for a single message and return a normalized message dict.

        Returns None if no message arrived within ``timeout_s`` seconds.
        The returned dict contains:
          ``topic``, ``partition``, ``offset``, ``key``, ``value_bytes``,
          ``headers``, ``timestamp``.

        Raises KafkaConsumerError on unrecoverable poll errors.
        """
        if self._consumer is None:
            raise KafkaConsumerError("Consumer not started. Call start() first.")
        try:
            msg = self._consumer.poll(timeout=timeout_s)
        except Exception as exc:
            raise KafkaConsumerError(f"Kafka poll error: {exc}") from exc

        if msg is None:
            return None
        if msg.error():
            err = msg.error()
            raise KafkaConsumerError(
                f"Kafka consumer error: {err}", upstream_code=err.code()
            )

        headers = {}
        if msg.headers():
            for k, v in msg.headers():
                headers[k] = v.decode("utf-8") if isinstance(v, bytes) else v

        key_raw = msg.key()
        key_str: str | None = (
            key_raw.decode("utf-8") if isinstance(key_raw, bytes) else key_raw
        )

        ts_type, ts_ms = msg.timestamp()
        return {
            "topic": msg.topic(),
            "partition": msg.partition(),
            "offset": msg.offset(),
            "key": key_str,
            "value_bytes": msg.value(),
            "headers": headers,
            "timestamp": ts_ms,
        }

    async def commit(self) -> None:
        """Commit the current consumer position (synchronous commit).

        Call this only after the message has been durably handed off.
        """
        if self._consumer is None:
            raise KafkaConsumerError("Consumer not started. Call start() first.")
        try:
            self._consumer.commit(asynchronous=False)
        except Exception as exc:
            raise KafkaConsumerError(f"Kafka commit error: {exc}") from exc

    async def close(self) -> None:
        """Close the consumer and release broker connections."""
        if self._consumer is not None:
            try:
                self._consumer.close()
            except Exception:
                pass
            finally:
                self._consumer = None
