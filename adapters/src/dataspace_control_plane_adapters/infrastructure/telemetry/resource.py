"""OpenTelemetry Resource builder.

Constructs the OTel Resource that identifies this service instance to the
collector. Resource attributes follow the OTel semantic conventions.
"""
from __future__ import annotations

from .config import TelemetrySettings


def build_resource(cfg: TelemetrySettings) -> "opentelemetry.sdk.resources.Resource":
    """Build an OTel Resource for the dataspace control plane service.

    Resource attributes populated:
    - ``service.name``             — logical service name (e.g. dataspace-control-plane)
    - ``service.version``          — semver of the running build
    - ``deployment.environment``   — environment label (development, staging, production)

    Args:
        cfg: TelemetrySettings populated from environment or defaults.

    Returns:
        opentelemetry.sdk.resources.Resource instance.
    """
    # Heavy SDK import deferred to avoid mandatory dependency at module load time.
    from opentelemetry.sdk.resources import Resource  # type: ignore[import]

    return Resource.create(
        {
            "service.name": cfg.service_name,
            "service.version": cfg.service_version,
            "deployment.environment": cfg.environment,
        }
    )
