from typing import Protocol, runtime_checkable
from datetime import datetime
from dataspace_control_plane_core.domains._shared.ids import TenantId
from .record import AuditRecord, AuditCategory


@runtime_checkable
class AuditSinkPort(Protocol):
    """Append-only sink. Adapter implements; never reads back through core."""

    async def emit(self, record: AuditRecord) -> None: ...


@runtime_checkable
class AuditQueryPort(Protocol):
    """Read-only query for operator audit trails."""

    async def list_records(
        self,
        tenant_id: TenantId,
        category: AuditCategory | None,
        from_dt: datetime,
        to_dt: datetime,
        limit: int = 100,
    ) -> list[AuditRecord]: ...

    async def get_record(self, tenant_id: TenantId, record_id: str) -> AuditRecord: ...
