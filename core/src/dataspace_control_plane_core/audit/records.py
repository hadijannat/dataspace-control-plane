"""Append-only audit and evidentiary record primitives."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from dataspace_control_plane_core.canonical_models.enums import RedactionClass, RetentionClass
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from dataspace_control_plane_core.domains._shared.ids import (
    LegalEntityId,
    TenantId,
    default_id_factory,
)
from dataspace_control_plane_core.domains._shared.time import utc_now


class AuditCategory(str, Enum):
    TRUST = "trust"
    TENANCY = "tenancy"
    CONTRACT = "contract"
    COMPLIANCE = "compliance"
    DATA_EXCHANGE = "data_exchange"
    ADMIN = "admin"
    SECURITY = "security"


class AuditOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    DENIED = "denied"


@dataclass(frozen=True)
class AuditActor:
    subject: str
    actor_type: str
    display_name: str | None = None

    @classmethod
    def from_actor_ref(cls, actor: ActorRef) -> "AuditActor":
        return cls(
            subject=actor.subject,
            actor_type=actor.actor_type.value,
            display_name=actor.display_name,
        )


@dataclass(frozen=True)
class AuditSubject:
    subject_id: str
    subject_type: str


@dataclass(frozen=True)
class AuditRecord:
    record_id: str
    tenant_id: TenantId
    occurred_at: datetime
    category: AuditCategory
    action: str
    outcome: AuditOutcome
    actor: AuditActor
    subject: AuditSubject
    correlation: CorrelationContext
    legal_entity_id: LegalEntityId | None = None
    pack_ids: tuple[str, ...] = ()
    detail: dict[str, Any] = field(default_factory=dict)
    retention_class: RetentionClass = RetentionClass.SEVEN_YEARS
    redaction_class: RedactionClass = RedactionClass.NONE

    @property
    def subject_id(self) -> str:
        return self.subject.subject_id

    @property
    def subject_type(self) -> str:
        return self.subject.subject_type

    @property
    def correlation_id(self):
        return self.correlation.correlation_id

    @property
    def causation_id(self):
        return self.correlation.causation_id

    @property
    def workflow_id(self):
        return self.correlation.workflow_id

    @classmethod
    def new(
        cls,
        tenant_id: TenantId,
        category: AuditCategory,
        action: str,
        outcome: AuditOutcome,
        actor: ActorRef,
        correlation: CorrelationContext,
        *,
        subject_id: str = "",
        subject_type: str = "",
        legal_entity_id: LegalEntityId | None = None,
        pack_ids: tuple[str, ...] = (),
        detail: dict[str, Any] | None = None,
        retention_class: RetentionClass = RetentionClass.SEVEN_YEARS,
        redaction_class: RedactionClass = RedactionClass.NONE,
    ) -> "AuditRecord":
        return cls(
            record_id=default_id_factory().new_request_id(),
            tenant_id=tenant_id,
            occurred_at=utc_now(),
            category=category,
            action=action,
            outcome=outcome,
            actor=AuditActor.from_actor_ref(actor),
            subject=AuditSubject(subject_id=subject_id, subject_type=subject_type),
            correlation=correlation,
            legal_entity_id=legal_entity_id,
            pack_ids=pack_ids,
            detail=detail or {},
            retention_class=retention_class,
            redaction_class=redaction_class,
        )
