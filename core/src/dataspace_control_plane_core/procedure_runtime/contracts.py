"""Deprecated compatibility facade. Prefer ``workflow_contracts`` and friends."""
from .procedure_ids import ProcedureHandle, ProcedureType
from .workflow_contracts import ProcedureInput, ProcedureResult, ProcedureStatus

__all__ = [
    "ProcedureHandle",
    "ProcedureInput",
    "ProcedureResult",
    "ProcedureStatus",
    "ProcedureType",
]
