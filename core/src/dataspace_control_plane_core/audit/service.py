from dataspace_control_plane_core.domains._shared.ids import TenantId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from .record import AuditRecord, AuditCategory, AuditOutcome
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
        **kwargs,
    ) -> AuditRecord:
        record = AuditRecord.new(
            tenant_id=tenant_id,
            category=category,
            action=action,
            outcome=outcome,
            actor=actor,
            correlation=correlation,
            **kwargs,
        )
        await self._sink.emit(record)
        return record
