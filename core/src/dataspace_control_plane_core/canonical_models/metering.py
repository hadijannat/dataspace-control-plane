"""Canonical metering and finops models."""
from __future__ import annotations
from datetime import datetime
from pydantic import field_validator

from .common import CanonicalBase


class UsageDimension(CanonicalBase):
    """A named dimension of usage (e.g. data_bytes_transferred, api_calls)."""
    name: str
    unit: str            # e.g. "bytes", "requests", "records"


class QuotaRef(CanonicalBase):
    """Reference to a quota definition."""
    quota_id: str
    dimension: UsageDimension
    limit_value: int
    window_seconds: int  # rolling or fixed window


class RatedUsage(CanonicalBase):
    """A rated usage line item derived from raw meter events."""
    meter_event_id: str
    agreement_id: str
    dimension: UsageDimension
    quantity: int
    rate_per_unit_minor: int   # in minor currency units
    currency_code: str
    rated_at: datetime


class MeterEventEnvelope(CanonicalBase):
    """Normalized meter event for ingest into the usage ledger."""
    event_id: str
    tenant_id: str
    legal_entity_id: str
    agreement_id: str
    policy_id: str
    asset_id: str
    counterparty_id: str
    dimension: UsageDimension
    quantity: int
    occurred_at: datetime
    source_system: str


class ChargeStatementEnvelope(CanonicalBase):
    """A statement of charges for a billing period."""
    statement_id: str
    tenant_id: str
    legal_entity_id: str
    period_start: datetime
    period_end: datetime
    line_items: list[RatedUsage] = []
    total_minor: int = 0
    currency_code: str = "EUR"
    finalized_at: datetime | None = None
