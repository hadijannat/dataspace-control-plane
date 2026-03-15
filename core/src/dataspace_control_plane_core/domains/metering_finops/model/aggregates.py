"""Aggregate roots for the metering_finops domain."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime

from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId
from dataspace_control_plane_core.domains._shared.errors import ConflictError
from .enums import ChargeStatementStatus, MeteringDimension, QuotaStatus
from .value_objects import UsageEvent, QuotaLimit

# Threshold fraction at which quota status transitions to APPROACHING_LIMIT.
_APPROACHING_THRESHOLD = 0.8


@dataclass
class MeteringLedger(AggregateRoot):
    """
    Ledger of raw usage events for a tenant / legal entity in a billing period.
    Events may only be appended while the ledger is in DRAFT state.
    """
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId("__unset__"))
    period_start: datetime = field(default_factory=lambda: __import__("datetime").datetime.min)
    period_end: datetime = field(default_factory=lambda: __import__("datetime").datetime.max)
    events: list[UsageEvent] = field(default_factory=list)
    status: ChargeStatementStatus = ChargeStatementStatus.DRAFT

    def record_event(self, event: UsageEvent) -> None:
        """
        Append a usage event to the ledger.
        Raises ConflictError if the ledger is not in DRAFT state.
        """
        if self.status != ChargeStatementStatus.DRAFT:
            raise ConflictError(
                f"MeteringLedger {self.id} is not in DRAFT state (current: {self.status.value}); "
                "cannot record new events",
                {"ledger_id": str(self.id), "status": self.status.value},
            )
        self.events.append(event)

    def finalize(self) -> None:
        """
        Transition the ledger to FINALIZED.
        Raises ConflictError if already finalized.
        """
        if self.status == ChargeStatementStatus.FINALIZED:
            raise ConflictError(
                f"MeteringLedger {self.id} is already finalized",
                {"ledger_id": str(self.id)},
            )
        self.status = ChargeStatementStatus.FINALIZED

    def total_for_dimension(self, dimension: MeteringDimension) -> int:
        """Return the sum of quantities for all events of the given dimension."""
        return sum(e.quantity for e in self.events if e.dimension == dimension)


@dataclass
class QuotaAllocation(AggregateRoot):
    """
    Quota ceiling configuration for a tenant / legal entity.
    Limits are keyed by MeteringDimension; the aggregate enforces at most one
    limit per dimension.
    """
    legal_entity_id: LegalEntityId = field(default_factory=lambda: LegalEntityId("__unset__"))
    limits: list[QuotaLimit] = field(default_factory=list)

    def set_limit(self, limit: QuotaLimit) -> None:
        """
        Replace an existing limit for the same dimension, or append if absent.
        """
        self.limits = [l for l in self.limits if l.dimension != limit.dimension]
        self.limits.append(limit)

    def check_quota(self, dimension: MeteringDimension, current_usage: int) -> QuotaStatus:
        """
        Evaluate current_usage against the configured limit for the dimension.
        Returns WITHIN_QUOTA if no limit is configured for the dimension.
        """
        for limit in self.limits:
            if limit.dimension == dimension:
                if current_usage >= limit.limit:
                    return QuotaStatus.QUOTA_EXCEEDED
                if limit.limit > 0 and current_usage / limit.limit >= _APPROACHING_THRESHOLD:
                    return QuotaStatus.APPROACHING_LIMIT
                return QuotaStatus.WITHIN_QUOTA
        return QuotaStatus.WITHIN_QUOTA
