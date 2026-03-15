"""Health probe for the SQL extract adapter."""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.health import (
    HealthProbe,
    HealthReport,
    HealthStatus,
)

from .config import SqlExtractSettings


class SqlExtractHealthProbe:
    """Configuration-backed readiness probe for SQL snapshot/watermark extraction."""

    def __init__(self, settings: SqlExtractSettings, adapter_name: str = "sql_extract") -> None:
        self._settings = settings
        self._adapter_name = adapter_name

    async def check(self) -> HealthReport:
        return HealthReport(
            adapter=self._adapter_name,
            status=HealthStatus.OK,
            message="SQL extract configuration loaded",
            details={
                "host": self._settings.host,
                "database": self._settings.database,
                "source_schema": self._settings.source_schema,
            },
        )

    def capability_descriptor(self) -> dict:
        return {
            "adapter": self._adapter_name,
            "type": "sql",
            "capabilities": [
                "introspection",
                "snapshot_extract",
                "watermark_extract",
                "postgres_cdc",
            ],
            "source_schema": self._settings.source_schema,
            "watermark_column": self._settings.watermark_column,
            "version": "0.1.0",
        }


_: HealthProbe = SqlExtractHealthProbe.__new__(SqlExtractHealthProbe)  # type: ignore[type-abstract]
