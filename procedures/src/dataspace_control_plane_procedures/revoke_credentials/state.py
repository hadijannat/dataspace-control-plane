from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RevocationWorkflowState:
    # revocation_requested | status_updated | bindings_propagated
    # | dependent_procedures_notified | evidence_complete
    revocation_state: str = "revocation_requested"
    revocation_ref: str = ""
    notified_procedure_ids: list[str] = field(default_factory=list)
    binding_update_refs: list[str] = field(default_factory=list)
    evidence_ref: str = ""
    issuer_confirmed: bool = False
