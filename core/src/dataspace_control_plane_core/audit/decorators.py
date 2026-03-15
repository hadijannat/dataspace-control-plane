from contextlib import asynccontextmanager
from typing import AsyncGenerator
from dataspace_control_plane_core.domains._shared.ids import TenantId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from .record import AuditCategory, AuditOutcome
from .service import AuditService


@asynccontextmanager
async def audit_action(
    service: AuditService,
    tenant_id: TenantId,
    category: AuditCategory,
    action: str,
    actor: ActorRef,
    correlation: CorrelationContext,
    **kwargs,
) -> AsyncGenerator[None, None]:
    try:
        yield
        await service.emit(tenant_id, category, action, AuditOutcome.SUCCESS, actor, correlation, **kwargs)
    except Exception:
        await service.emit(tenant_id, category, action, AuditOutcome.FAILURE, actor, correlation, **kwargs)
        raise
