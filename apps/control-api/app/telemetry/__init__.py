"""OpenTelemetry setup (traces + metrics). Called from lifespan if otel_endpoint is set."""
from app.settings import settings


def setup_telemetry() -> None:
    if not settings.otel_endpoint:
        return
    # TODO: configure OTLP exporter, FastAPI instrumentation, Temporal interceptors
