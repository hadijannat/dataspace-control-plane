"""Value objects for the metering_finops domain."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

from dataspace_control_plane_core.domains._shared.money import Money
from .enums import MeteringDimension


@dataclass(frozen=True)
class UsageEvent:
    """
    A single metered usage event. event_id is caller-assigned for idempotency.
    quantity is always a non-negative integer in the named unit.
    """
    event_id: str
    dimension: MeteringDimension
    quantity: int
    unit: str
    occurred_at: datetime
    agreement_id: str | None
    asset_id: str | None


@dataclass(frozen=True)
class QuotaLimit:
    """
    A quota ceiling for a single dimension over a rolling period expressed in days.
    """
    dimension: MeteringDimension
    limit: int
    period_days: int


@dataclass(frozen=True)
class ChargeLineItem:
    """
    A single line in a charge statement: dimension, quantity consumed, per-unit price,
    and the pre-calculated total.
    """
    dimension: MeteringDimension
    quantity: int
    unit_price: Money
    total: Money
