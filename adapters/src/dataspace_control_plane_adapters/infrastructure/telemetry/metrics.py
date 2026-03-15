"""OpenTelemetry metrics adapter.

Implements core/domains/observability/ports.py MetricEmitterPort using the OTel SDK.
Exports metric data to the configured OTLP/gRPC endpoint via a PeriodicExportingMetricReader.

Metric kinds (from core MetricDefinition.kind):
  COUNTER   -> OTel Counter (monotonically increasing)
  GAUGE     -> OTel ObservableGauge (last-value semantics, recorded as UpDownCounter)
  HISTOGRAM -> OTel Histogram
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .config import TelemetrySettings

if TYPE_CHECKING:
    from dataspace_control_plane_core.domains.observability.model.value_objects import MetricDefinition
    from dataspace_control_plane_core.domains.observability.model.enums import MetricKind

logger = logging.getLogger(__name__)


class OtelMetricAdapter:
    """Implements MetricEmitterPort using the OpenTelemetry SDK metrics API.

    # implements core/domains/observability/ports.py MetricEmitterPort

    Instruments are created lazily on first use and cached by metric name
    to avoid per-call overhead.
    """

    def __init__(self, cfg: TelemetrySettings) -> None:
        self._cfg = cfg
        self._meter = self._setup_metrics(cfg)
        self._instruments: dict[str, Any] = {}

    def _setup_metrics(self, cfg: TelemetrySettings) -> "opentelemetry.metrics.Meter":
        """Configure MeterProvider, OTLP exporter, and periodic metric reader."""
        from opentelemetry.sdk.metrics import MeterProvider  # type: ignore[import]
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader  # type: ignore[import]
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (  # type: ignore[import]
            OTLPMetricExporter,
        )
        from opentelemetry import metrics  # type: ignore[import]
        from .resource import build_resource

        resource = build_resource(cfg)
        exporter = OTLPMetricExporter(
            endpoint=cfg.otlp_endpoint,
            insecure=cfg.insecure,
        )
        reader = PeriodicExportingMetricReader(
            exporter,
            export_interval_millis=cfg.export_interval_ms,
            export_timeout_millis=cfg.export_timeout_ms,
        )
        provider = MeterProvider(resource=resource, metric_readers=[reader])
        metrics.set_meter_provider(provider)
        return metrics.get_meter(cfg.service_name, cfg.service_version)

    def increment(
        self,
        metric: "MetricDefinition",
        value: float,
        labels: dict[str, str],
    ) -> None:
        """Increment a counter metric by *value*.

        # implements MetricEmitterPort.increment

        Intended for COUNTER kind MetricDefinitions. If the MetricDefinition
        has kind GAUGE or HISTOGRAM, increment falls back to record().

        Args:
            metric: MetricDefinition from core/observability.
            value:  Amount to add (must be >= 0 for counters).
            labels: Label key-value pairs matching the metric's declared labels.
        """
        from dataspace_control_plane_core.domains.observability.model.enums import MetricKind

        if metric.kind != MetricKind.COUNTER:
            logger.debug(
                "increment() called on non-counter metric %s (kind=%s); delegating to record()",
                metric.name, metric.kind,
            )
            self.record(metric, value, labels)
            return

        instrument = self._get_or_create_counter(metric)
        instrument.add(value, attributes=labels)

    def record(
        self,
        metric: "MetricDefinition",
        value: float,
        labels: dict[str, str],
    ) -> None:
        """Record a metric observation.

        # implements MetricEmitterPort.record

        Dispatches to the appropriate OTel instrument based on MetricDefinition.kind:
        - COUNTER   -> Counter.add(value)
        - GAUGE     -> UpDownCounter.add(value) (approximates gauge with last-value semantics)
        - HISTOGRAM -> Histogram.record(value)

        Args:
            metric: MetricDefinition from core/observability.
            value:  Observed value.
            labels: Label key-value pairs.
        """
        from dataspace_control_plane_core.domains.observability.model.enums import MetricKind

        if metric.kind == MetricKind.COUNTER:
            self._get_or_create_counter(metric).add(value, attributes=labels)
        elif metric.kind == MetricKind.GAUGE:
            self._get_or_create_updown_counter(metric).add(value, attributes=labels)
        elif metric.kind == MetricKind.HISTOGRAM:
            self._get_or_create_histogram(metric).record(value, attributes=labels)
        else:
            logger.warning("Unknown MetricKind %s for metric %s; skipping.", metric.kind, metric.name)

    # --- Instrument factory helpers -----------------------------------------------

    def _get_or_create_counter(self, metric: "MetricDefinition") -> Any:
        key = f"counter:{metric.name}"
        if key not in self._instruments:
            self._instruments[key] = self._meter.create_counter(
                name=metric.name,
                unit=metric.unit,
                description=metric.description,
            )
        return self._instruments[key]

    def _get_or_create_updown_counter(self, metric: "MetricDefinition") -> Any:
        key = f"updown:{metric.name}"
        if key not in self._instruments:
            self._instruments[key] = self._meter.create_up_down_counter(
                name=metric.name,
                unit=metric.unit,
                description=metric.description,
            )
        return self._instruments[key]

    def _get_or_create_histogram(self, metric: "MetricDefinition") -> Any:
        key = f"histogram:{metric.name}"
        if key not in self._instruments:
            self._instruments[key] = self._meter.create_histogram(
                name=metric.name,
                unit=metric.unit,
                description=metric.description,
            )
        return self._instruments[key]
