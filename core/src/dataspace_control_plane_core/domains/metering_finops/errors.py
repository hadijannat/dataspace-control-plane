"""Domain errors for the metering_finops domain."""
from __future__ import annotations

from dataspace_control_plane_core.domains._shared.errors import (
    DomainError,
    NotFoundError,
    ConflictError,
)


class LedgerNotFoundError(NotFoundError):
    """Raised when a MeteringLedger cannot be located by ID."""


class QuotaAllocationNotFoundError(NotFoundError):
    """Raised when a QuotaAllocation cannot be located for a tenant / legal entity."""


class LedgerAlreadyFinalizedError(ConflictError):
    """Raised when an operation attempts to mutate a finalized ledger."""


class QuotaExceededError(DomainError):
    """Raised when recorded usage would exceed a configured quota limit."""
