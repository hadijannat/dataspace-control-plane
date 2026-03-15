from typing import Protocol, runtime_checkable, Any
from .model.value_objects import MetricDefinition, StructuredLogEntry, TraceContext
from .model.enums import TraceStatus


@runtime_checkable
class MetricEmitterPort(Protocol):
    def increment(self, metric: MetricDefinition, value: float, labels: dict[str, str]) -> None: ...

    def record(self, metric: MetricDefinition, value: float, labels: dict[str, str]) -> None: ...


@runtime_checkable
class LogEmitterPort(Protocol):
    async def emit(self, entry: StructuredLogEntry) -> None: ...


@runtime_checkable
class TracingPort(Protocol):
    def start_span(self, name: str, trace_ctx: TraceContext | None) -> TraceContext: ...

    def end_span(self, ctx: TraceContext, status: TraceStatus, error: Exception | None) -> None: ...
