"""
Telemetry setup for temporal-workers.
Wire OTLP exporter here when infra/ provides the collector endpoint.
"""
from __future__ import annotations


def setup_telemetry(service_name: str = "temporal-workers") -> None:
    """
    Initialize OpenTelemetry tracing and metrics.
    Currently a no-op stub; configure once OTEL_EXPORTER_OTLP_ENDPOINT is available.
    """
    import os
    import structlog
    log = structlog.get_logger(__name__)
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if endpoint:
        log.info("telemetry.otlp_configured", endpoint=endpoint)
        # TODO: configure opentelemetry-sdk + otlp exporter here
    else:
        log.debug("telemetry.skipped", reason="OTEL_EXPORTER_OTLP_ENDPOINT not set")
