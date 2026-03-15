"""Telemetry infrastructure adapter.

OTLP-based runtime instrumentation. Implements the three core/observability/ ports:
MetricEmitterPort, LogEmitterPort, TracingPort.
Emits to an OpenTelemetry Collector endpoint (default: localhost:4317).
"""
from __future__ import annotations
