from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from dataspace_control_plane_core.domains._shared.ids import TenantId, AggregateId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from dataspace_control_plane_core.canonical_models.enums import RetentionClass, RedactionClass


class AuditCategory(str, Enum):
    TRUST = "trust"               # machine credentials, DID operations
    TENANCY = "tenancy"           # tenant registration, operator grants
    CONTRACT = "contract"         # negotiation, agreement, entitlement
    COMPLIANCE = "compliance"     # gap scans, policy evaluation
    DATA_EXCHANGE = "data_exchange"  # transfer initiations, completions
    ADMIN = "admin"               # operator actions, config changes
    SECURITY = "security"         # auth failures, anomalies


class AuditOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    DENIED = "denied"


@dataclass(frozen=True)
class AuditRecord:
    record_id: str
    tenant_id: TenantId
    occurred_at: datetime
    category: AuditCategory
    action: str                    # e.g. "tenant_topology.activate"
    outcome: AuditOutcome
    actor: ActorRef
    correlation: CorrelationContext
    subject_id: str = ""           # the aggregate/resource affected
    subject_type: str = ""
    detail: dict[str, Any] = field(default_factory=dict)
    retention_class: RetentionClass = RetentionClass.SEVEN_YEARS
    redaction_class: RedactionClass = RedactionClass.NONE

    @classmethod
    def new(
        cls,
        tenant_id: TenantId,
        category: AuditCategory,
        action: str,
        outcome: AuditOutcome,
        actor: ActorRef,
        correlation: CorrelationContext,
        **kwargs: Any,
    ) -> "AuditRecord":
        import uuid
        return cls(
            record_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            occurred_at=datetime.now(timezone.utc),
            category=category,
            action=action,
            outcome=outcome,
            actor=actor,
            correlation=correlation,
            **kwargs,
        )
