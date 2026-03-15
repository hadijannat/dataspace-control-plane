"""Health probe for the Kafka ingest adapter."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)

from .config import KafkaSettings


class KafkaHealthProbe:
    """Configuration-backed readiness probe for Kafka ingestion and publishing."""

    def __init__(self, settings: KafkaSettings, adapter_name: str = "kafka_ingest") -> None:
        self._settings = settings
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        return HealthReport(
            adapter=self._adapter_name,
            status=HealthStatus.OK,
            message="Kafka producer/consumer configuration loaded",
            details={
                "bootstrap_servers": self._settings.bootstrap_servers,
                "consumer_group_id": self._settings.consumer_group_id,
            },
        )

    def capability_descriptor(self) -> dict:
        return {
            "adapter": self._adapter_name,
            "type": "kafka",
            "capabilities": [
                "consumer",
                "producer",
                "dead_letter",
                "checkpointing",
                "idempotent_publish",
            ],
            "producer_idempotence": self._settings.producer_enable_idempotence,
            "version": "0.1.0",
        }


_: HealthProbe = KafkaHealthProbe.__new__(KafkaHealthProbe)  # type: ignore[type-abstract]
