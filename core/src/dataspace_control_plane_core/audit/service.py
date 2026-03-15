from dataspace_control_plane_core.domains._shared.ids import LegalEntityId, TenantId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from .records import AuditRecord, AuditCategory, AuditOutcome
from .ports import AuditSinkPort


class AuditService:
    def __init__(self, sink: AuditSinkPort) -> None:
        self._sink = sink

    async def emit(
        self,
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
        detail: dict | None = None,
        **kwargs,
    ) -> AuditRecord:
        record = AuditRecord.new(
            tenant_id=tenant_id,
            category=category,
            action=action,
            outcome=outcome,
            actor=actor,
            correlation=correlation,
            subject_id=subject_id,
            subject_type=subject_type,
            legal_entity_id=legal_entity_id,
            pack_ids=pack_ids,
            detail=detail,
            **kwargs,
        )
        await self._sink.emit(record)
        return record
