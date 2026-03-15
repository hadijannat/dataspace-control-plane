from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RevocationStartInput:
    tenant_id: str
    legal_entity_id: str
    subject: str
    credential_id: str
    credential_type: str
    revocation_reason: str
    revoked_by: str
    urgent: bool = True


@dataclass(frozen=True)
class RevocationResult:
    workflow_id: str
    status: str
    revocation_ref: str = ""
    notified_procedures: list[str] = field(default_factory=list)
    evidence_ref: str = ""


@dataclass
class RevocationStatusQuery:
    revocation_state: str
    revocation_ref: str
    notified_count: int
    is_complete: bool
