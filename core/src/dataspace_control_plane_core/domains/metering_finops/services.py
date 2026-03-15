"""Domain services for the metering_finops domain."""
from __future__ import annotations

from dataspace_control_plane_core.domains._shared.ids import AggregateId
from dataspace_control_plane_core.domains._shared.time import Clock, UtcClock
from .commands import (
    RecordUsageEventCommand,
    FinalizeLedgerCommand,
    SetQuotaLimitCommand,
)
from .model.aggregates import MeteringLedger, QuotaAllocation
from .ports import MeteringLedgerRepository, QuotaAllocationRepository


class MeteringService:
    """
    Orchestrates usage recording, ledger finalization, and quota management.
    Persistence is delegated to the injected repositories.
    """

    def __init__(
        self,
        ledgers: MeteringLedgerRepository,
        quotas: QuotaAllocationRepository,
        clock: Clock = UtcClock(),
    ) -> None:
        self._ledgers = ledgers
        self._quotas = quotas
        self._clock = clock

    async def record_usage(self, cmd: RecordUsageEventCommand) -> MeteringLedger:
        """Append a usage event to the specified ledger and persist."""
        ledger = await self._ledgers.get(cmd.tenant_id, cmd.ledger_id)
        ledger.record_event(cmd.event)
        await self._ledgers.save(cmd.tenant_id, ledger)
        return ledger

    async def finalize_ledger(self, cmd: FinalizeLedgerCommand) -> MeteringLedger:
        """Finalize the ledger (close the billing period) and persist."""
        ledger = await self._ledgers.get(cmd.tenant_id, cmd.ledger_id)
        ledger.finalize()
        await self._ledgers.save(cmd.tenant_id, ledger)
        return ledger

    async def set_quota(self, cmd: SetQuotaLimitCommand) -> QuotaAllocation:
        """
        Load (or create) the quota allocation for the legal entity, set the limit,
        and persist.
        """
        try:
            alloc = await self._quotas.get(cmd.tenant_id, cmd.legal_entity_id)
        except Exception:
            # If no allocation exists, create a fresh one.
            alloc = QuotaAllocation(
                id=AggregateId.generate(),
                tenant_id=cmd.tenant_id,
                legal_entity_id=cmd.legal_entity_id,
            )
        alloc.set_limit(cmd.limit)
        await self._quotas.save(cmd.tenant_id, alloc)
        return alloc
