"""Port interfaces for the metering_finops domain. Adapters implement these."""
from __future__ import annotations
from datetime import datetime
from typing import Protocol, runtime_checkable

from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId
from .model.aggregates import MeteringLedger, QuotaAllocation
from .model.value_objects import ChargeLineItem


@runtime_checkable
class MeteringLedgerRepository(Protocol):
    """Persistence port for MeteringLedger aggregates."""

    async def get(self, tenant_id: TenantId, ledger_id: AggregateId) -> MeteringLedger:
        """Load a MeteringLedger; raises LedgerNotFoundError if absent."""
        ...

    async def save(self, tenant_id: TenantId, ledger: MeteringLedger) -> None:
        """Persist the ledger with optimistic concurrency."""
        ...

    async def get_or_create_current(
        self,
        tenant_id: TenantId,
        legal_entity_id: LegalEntityId,
        period_start: datetime,
        period_end: datetime,
    ) -> MeteringLedger:
        """
        Return the existing DRAFT ledger for the period, or create and persist
        a new one if none exists.
        """
        ...


@runtime_checkable
class QuotaAllocationRepository(Protocol):
    """Persistence port for QuotaAllocation aggregates."""

    async def get(self, tenant_id: TenantId, legal_entity_id: LegalEntityId) -> QuotaAllocation:
        """Load a QuotaAllocation; raises QuotaAllocationNotFoundError if absent."""
        ...

    async def save(self, tenant_id: TenantId, alloc: QuotaAllocation) -> None:
        """Persist the quota allocation."""
        ...


@runtime_checkable
class BillingExportPort(Protocol):
    """Cross-boundary port: export a finalized charge statement to a billing system."""

    async def export_statement(
        self,
        tenant_id: TenantId,
        ledger: MeteringLedger,
        line_items: list[ChargeLineItem],
    ) -> str:
        """
        Export the statement and return an opaque export reference string
        (e.g. an external invoice ID or file path).
        """
        ...


UsageIngestPort = MeteringLedgerRepository
RatingEnginePort = BillingExportPort
QuotaEnforcerPort = QuotaAllocationRepository
