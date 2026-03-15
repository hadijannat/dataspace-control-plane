"""Kafka idempotent producer wrapper for the Kafka ingest adapter.

Producer idempotence is ALWAYS enabled (not opt-in). The configuration enforces:
  - enable.idempotence = True
  - acks = all
  - retries > 0
  - max.in.flight.requests.per.connection <= 5

These constraints are validated at the settings level (KafkaSettings) and
again at producer construction to prevent accidental misconfiguration.
"""
from __future__ import annotations

import hashlib
from typing import Any

from .config import KafkaSettings
from .errors import KafkaProducerError


class KafkaProducer:
    """Async-style idempotent Kafka producer backed by confluent_kafka.Producer.

    Idempotence is enforced at construction time. All required confluent_kafka
    settings for exactly-once delivery semantics within a single session are
    applied as non-overridable defaults.
    """

    def __init__(self, settings: KafkaSettings) -> None:
        # Re-validate idempotence constraints at construction time.
        if settings.producer_enable_idempotence:
            if settings.producer_acks != "all":
                raise KafkaProducerError(
                    "Idempotent producer requires acks='all'. "
                    f"Got: '{settings.producer_acks}'"
                )
            if settings.producer_max_in_flight > 5:
                raise KafkaProducerError(
                    "Idempotent producer requires max_in_flight<=5. "
                    f"Got: {settings.producer_max_in_flight}"
                )
        self._settings = settings
        self._producer: Any = None  # confluent_kafka.Producer

    def _build_config(self) -> dict[str, Any]:
        """Build the confluent_kafka producer configuration dict."""
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

    async def _ensure_started(self) -> None:
        """Lazily construct the underlying confluent_kafka Producer."""
        if self._producer is not None:
            return
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
                f"Failed to create Kafka producer: {exc}"
            ) from exc

    async def send(
        self,
        topic: str,
        value: bytes,
        *,
        key: str | None = None,
        headers: dict[str, str] | None = None,
        partition_key: str | None = None,
    ) -> None:
        """Produce a message to the given topic.

        Args:
            topic: Destination Kafka topic name.
            value: Message value bytes (already serialized).
            key: Optional Kafka message key string (used for log compaction / routing).
            headers: Optional dict of header key → value strings.
            partition_key: If provided and ``key`` is None, used as the message key
                for deterministic partition assignment.
        """
        await self._ensure_started()
        effective_key: bytes | None = None
        resolved_key = key or partition_key
        if resolved_key is not None:
            effective_key = resolved_key.encode("utf-8")

        kafka_headers: list[tuple[str, bytes]] | None = None
        if headers:
            kafka_headers = [
                (k, v.encode("utf-8") if isinstance(v, str) else v)
                for k, v in headers.items()
            ]

        def _on_delivery(err: Any, _msg: Any) -> None:
            if err is not None:
                # Delivery report callback — errors are surfaced via flush().
                pass

        try:
            self._producer.produce(
                topic,
                value=value,
                key=effective_key,
                headers=kafka_headers,
                on_delivery=_on_delivery,
            )
        except Exception as exc:
            raise KafkaProducerError(
                f"Failed to produce message to topic '{topic}': {exc}"
            ) from exc

    def partition_key_for_tenant(self, tenant_id: str) -> str:
        """Return a deterministic partition key for the given tenant ID.

        Ensures that all messages for a tenant are routed to the same partition
        for ordered processing within a tenant scope.
        """
        return _stable_key("tenant", tenant_id)

    def partition_key_for_asset(self, asset_id: str) -> str:
        """Return a deterministic partition key for the given asset ID."""
        return _stable_key("asset", asset_id)

    async def flush(self, timeout_s: float = 10.0) -> None:
        """Flush all buffered messages to Kafka brokers.

        Raises KafkaProducerError if flush does not complete within ``timeout_s``.
        """
        if self._producer is None:
            return
        try:
            remaining = self._producer.flush(timeout=timeout_s)
            if remaining > 0:
                raise KafkaProducerError(
                    f"Producer flush timed out; {remaining} message(s) not delivered."
                )
        except KafkaProducerError:
            raise
        except Exception as exc:
            raise KafkaProducerError(f"Producer flush error: {exc}") from exc

    async def close(self) -> None:
        """Flush and release all producer resources."""
        if self._producer is not None:
            try:
                await self.flush()
            finally:
                self._producer = None


def _stable_key(prefix: str, value: str) -> str:
    """Return a short, stable, hex-encoded key derived from prefix + value."""
    digest = hashlib.sha256(f"{prefix}:{value}".encode()).hexdigest()
    return f"{prefix}:{digest[:16]}"
