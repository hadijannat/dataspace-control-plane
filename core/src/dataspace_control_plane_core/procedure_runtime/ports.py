from typing import Protocol, runtime_checkable, Any
from .contracts import ProcedureHandle, ProcedureInput, ProcedureResult, ProcedureStatus, ProcedureType
from dataspace_control_plane_core.domains._shared.ids import WorkflowId, TenantId


@runtime_checkable
class WorkflowGatewayPort(Protocol):
    """Implemented by apps/temporal-workers; core never imports Temporal SDK."""

    async def start(self, inp: ProcedureInput) -> ProcedureHandle: ...

    async def get_status(self, tenant_id: TenantId, workflow_id: WorkflowId) -> ProcedureResult: ...

    async def cancel(self, tenant_id: TenantId, workflow_id: WorkflowId, reason: str) -> None: ...

    async def signal(
        self,
        tenant_id: TenantId,
        workflow_id: WorkflowId,
        signal: str,
        payload: dict[str, Any],
    ) -> None: ...


@runtime_checkable
class ProcedureRegistryPort(Protocol):
    """Read by apps/temporal-workers at startup to wire workflow/activity types."""

    def list_workflow_types(self, procedure_type: ProcedureType) -> list[str]: ...

    def list_activity_types(self, task_queue: str) -> list[str]: ...
