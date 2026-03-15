from __future__ import annotations

from dataclasses import dataclass

# Re-export for convenience
from .input import ConnectorStatusQuery  # noqa: F401


@dataclass(frozen=True)
class HealthDegraded:
    """Signal: runtime health check has detected a degraded connector."""
    event_id: str
    reason: str


@dataclass(frozen=True)
class WalletBound:
    """Signal: wallet credentials have been bound to this connector."""
    event_id: str
    wallet_ref: str


@dataclass(frozen=True)
class ForceHealthCheckInput:
    """Update input: trigger an immediate health check."""
    requested_by: str = ""


@dataclass(frozen=True)
class ForceHealthCheckResult:
    """Update result: health status string after the forced check."""
    health_status: str
    is_healthy: bool
