"""Telemetry adapter configuration.

All OpenTelemetry connection parameters are loaded from environment variables
with the OTEL_ prefix, consistent with the OpenTelemetry specification for
SDK configuration.
"""
from __future__ import annotations

from pydantic import Field
from pydantic_settings import SettingsConfigDict

from dataspace_control_plane_adapters._shared.config import AdapterSettings


class TelemetrySettings(AdapterSettings):
    """Configuration for the OTLP telemetry infrastructure adapter.

    Source order (highest wins): environment variables, .env file, defaults.
    All env vars are prefixed with OTEL_ (case-insensitive).

    The OTLP endpoint is the gRPC address of the OpenTelemetry Collector.
    For local development, this is typically http://localhost:4317.
    For production, point to the collector deployed in the same namespace.
    """

    model_config = SettingsConfigDict(
        env_prefix="OTEL_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    otlp_endpoint: str = Field(
        default="http://localhost:4317",
        description="gRPC endpoint of the OpenTelemetry Collector (OTLP/gRPC).",
    )
    service_name: str = Field(
        default="dataspace-control-plane",
        description="Logical service name reported to the collector.",
    )
    service_version: str = Field(
        default="0.1.0",
        description="Service version reported to the collector.",
    )
    environment: str = Field(
        default="development",
        description="Deployment environment (development, staging, production).",
    )
    export_interval_ms: int = Field(
        default=5000,
        description="Metric export interval in milliseconds.",
    )
    export_timeout_ms: int = Field(
        default=10000,
        description="Export timeout in milliseconds before giving up on a batch.",
    )
    # Trace sampling
    traces_sampler: str = Field(
        default="parentbased_always_on",
        description="OTel trace sampler type (parentbased_always_on, always_off, traceidratio).",
    )
    traces_sampler_arg: str = Field(
        default="1.0",
        description="Argument for the sampler (e.g. ratio for traceidratio sampler).",
    )
    # gRPC connection tuning
    insecure: bool = Field(
        default=True,
        description="Use insecure gRPC connection to the collector (no TLS). "
                    "Set False in production and configure TLS.",
    )
