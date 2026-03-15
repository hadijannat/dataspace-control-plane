"""Health and readiness probe abstractions for all adapters.

Every concrete adapter must expose a health probe. Apps use these probes
to populate /readyz and /healthz endpoints.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol, runtime_checkable


class HealthStatus(str, Enum):
    OK = "ok"
    DEGRADED = "degraded"
    DOWN = "down"


@dataclass(frozen=True)
class HealthReport:
    adapter: str
    status: HealthStatus
    message: str = ""
    details: dict = field(default_factory=dict)

    @property
    def is_healthy(self) -> bool:
        return self.status == HealthStatus.OK


@runtime_checkable
class HealthProbe(Protocol):
    """Every adapter must implement this protocol."""

    async def check(self) -> HealthReport:
        """Return a HealthReport describing the adapter's current state."""
        ...

    def capability_descriptor(self) -> dict:
        """Return a dict describing the adapter's identity, version, and capabilities."""
        ...


class AlwaysHealthyProbe:
    """Stub probe for adapters that have no meaningful connectivity check yet."""

    def __init__(self, adapter_name: str) -> None:
        self._name = adapter_name

    async def check(self) -> HealthReport:
        return HealthReport(adapter=self._name, status=HealthStatus.OK, message="stub probe")

    def capability_descriptor(self) -> dict:
        return {"adapter": self._name, "capabilities": [], "version": "0.1.0"}
