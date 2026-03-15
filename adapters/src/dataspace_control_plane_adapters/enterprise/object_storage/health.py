"""Health probe for the object-storage adapter."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)

from .config import ObjectStorageSettings


class ObjectStorageHealthProbe:
    """Configuration-backed readiness probe for blob storage access."""

    def __init__(
        self,
        settings: ObjectStorageSettings,
        adapter_name: str = "object_storage",
    ) -> None:
        self._settings = settings
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        return HealthReport(
            adapter=self._adapter_name,
            status=HealthStatus.OK,
            message="Object storage configuration loaded",
            details={
                "bucket": self._settings.default_bucket,
                "endpoint_url": self._settings.endpoint_url or "aws-default",
            },
        )

    def capability_descriptor(self) -> dict:
        return {
            "adapter": self._adapter_name,
            "type": "object-storage",
            "capabilities": [
                "streaming_reader",
                "streaming_writer",
                "multipart_upload",
                "digest_verification",
            ],
            "bucket": self._settings.default_bucket,
            "version": "0.1.0",
        }


_: HealthProbe = ObjectStorageHealthProbe.__new__(ObjectStorageHealthProbe)  # type: ignore[type-abstract]
