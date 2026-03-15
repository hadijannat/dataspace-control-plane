"""Domain invariants for the metering_finops domain."""
from __future__ import annotations

from dataspace_control_plane_core.domains._shared.errors import ValidationError
from .enums import ChargeStatementStatus


def require_draft_ledger(ledger: object) -> None:
    """Raise ValidationError if the ledger is not in DRAFT state."""
    from .aggregates import MeteringLedger
    assert isinstance(ledger, MeteringLedger)
    if ledger.status != ChargeStatementStatus.DRAFT:
        raise ValidationError(
            f"MeteringLedger {ledger.id} must be in DRAFT state but is {ledger.status.value}",
            {"ledger_id": str(ledger.id), "status": ledger.status.value},
        )


def require_period_valid(ledger: object) -> None:
    """Raise ValidationError if period_end is not strictly after period_start."""
    from .aggregates import MeteringLedger
    assert isinstance(ledger, MeteringLedger)
    if ledger.period_end <= ledger.period_start:
        raise ValidationError(
            f"MeteringLedger {ledger.id}: period_end must be after period_start",
            {
                "ledger_id": str(ledger.id),
                "period_start": str(ledger.period_start),
                "period_end": str(ledger.period_end),
            },
        )
