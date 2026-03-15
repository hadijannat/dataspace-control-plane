"""Telemetry adapter-specific error hierarchy.

Rules:
- TelemetryError is the root of all telemetry-layer exceptions.
- Export errors are non-fatal by design: the control plane must not fail on
  telemetry errors. Callers should log and continue.
- Never expose secrets or payload content in error messages.
"""
from __future__ import annotations

from dataspace_control_plane_adapters._shared.errors import AdapterError


class TelemetryError(AdapterError):
    """Root for all telemetry infrastructure adapter errors."""


class TelemetryExportError(TelemetryError):
    """Raised when OTLP export to the collector fails.

    This error is treated as non-fatal by convention: the control plane
    continues operating even if telemetry export is degraded.
    """

    def __init__(
        self,
        signal: str,
        message: str,
        *,
        upstream_code: str | int | None = None,
    ) -> None:
        super().__init__(
            f"OTLP export failed for signal={signal!r}: {message}",
            upstream_code=upstream_code,
        )
        self.signal = signal


class TelemetryInitError(TelemetryError):
    """Raised when the telemetry provider fails to initialise at startup."""
