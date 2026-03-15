from typing import Any, Protocol, runtime_checkable

from dataspace_control_plane_core.domains._shared.ids import TenantId, WorkflowId

from .messages import (
    ApproveProcedure,
    CancelProcedure,
    PauseProcedure,
    ProcedureQuery,
    ProcedureQueryResponse,
    RejectProcedure,
    ResumeProcedure,
    RetryProcedure,
)
from .procedure_ids import ProcedureHandle, ProcedureType
from .workflow_contracts import ProcedureInput, ProcedureResult


@runtime_checkable
class WorkflowGatewayPort(Protocol):
    """Implemented by runtime owners; `core` remains workflow-engine agnostic."""

    async def start(self, inp: ProcedureInput) -> ProcedureHandle:
        ...

    async def get_status(self, tenant_id: TenantId, workflow_id: WorkflowId) -> ProcedureResult:
        ...

    async def cancel(self, message: CancelProcedure) -> None:
        ...

    async def approve(self, message: ApproveProcedure) -> None:
        ...

    async def reject(self, message: RejectProcedure) -> None:
        ...

    async def pause(self, message: PauseProcedure) -> None:
        ...

    async def resume(self, message: ResumeProcedure) -> None:
        ...

    async def retry(self, message: RetryProcedure) -> None:
        ...

    async def signal(
        self,
        tenant_id: TenantId,
        workflow_id: WorkflowId,
        signal: str,
        payload: dict[str, Any],
    ) -> None:
        ...

    async def query(self, message: ProcedureQuery) -> ProcedureQueryResponse:
        ...


@runtime_checkable
class ProcedureRegistryPort(Protocol):
    """Runtime registry used by workers to wire procedures and activities."""

    def list_workflow_types(self, procedure_type: ProcedureType) -> list[str]:
        ...

    def list_activity_types(self, task_queue: str) -> list[str]:
        ...
