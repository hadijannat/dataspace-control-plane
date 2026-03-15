"""Temporal WorkflowGatewayPort implementation.

Implements core/procedure_runtime/ports.py WorkflowGatewayPort using the
temporalio.client.Client wrapper helpers in this package.

This module is the authoritative wiring point between the core port contract
and the Temporal SDK. Apps/temporal-workers inject TemporalWorkflowGateway
into procedure services via dependency injection at container startup.
"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    import temporalio.client
    from dataspace_control_plane_core.procedure_runtime.contracts import (
        ProcedureHandle,
        ProcedureInput,
        ProcedureResult,
        ProcedureStatus,
    )
    from dataspace_control_plane_core.domains._shared.ids import TenantId, WorkflowId

from .workflow_handles import WorkflowHandleHelper
from .signals import SignalSender
from .queries import QueryExecutor
from .errors import TemporalRpcError, WorkflowNotFoundError

logger = logging.getLogger(__name__)


class TemporalWorkflowGateway:
    """Implements WorkflowGatewayPort using the Temporal client.

    # implements core/procedure_runtime/ports.py WorkflowGatewayPort

    This class is the sole entry point for workflow lifecycle management
    from the adapters layer. Only apps/ and activity code should instantiate
    or inject this class — procedure code in procedures/ must never import it.

    Dependency contract:
    - Requires a connected temporalio.client.Client.
    - Translates ProcedureInput/Handle domain objects into Temporal SDK calls.
    - Translates Temporal SDK results into core ProcedureResult objects.
    """

    def __init__(
        self,
        client: "temporalio.client.Client",
        *,
        default_task_queue: str = "dataspace-control-plane",
    ) -> None:
        self._helper = WorkflowHandleHelper(client)
        self._signal_sender = SignalSender(client)
        self._query_executor = QueryExecutor(client)
        self._default_task_queue = default_task_queue

    async def start(self, inp: "ProcedureInput") -> "ProcedureHandle":
        """Start a Temporal workflow from a ProcedureInput domain object.

        # implements WorkflowGatewayPort.start

        Maps ProcedureInput fields to Temporal start arguments:
        - inp.procedure_type.value -> workflow_type
        - inp.idempotency_key or generated UUID -> workflow_id
        - inp.payload -> input
        - default_task_queue -> task_queue

        Returns:
            ProcedureHandle with the workflow_id and run_id populated.

        Raises:
            WorkflowAlreadyStartedError: Workflow with same id is already running.
            TemporalRpcError: Any other Temporal error.
        """
        # Deferred core imports: adapters may import core but never the reverse.
        from dataspace_control_plane_core.procedure_runtime.contracts import ProcedureHandle
        from dataspace_control_plane_core.domains._shared.ids import WorkflowId

        workflow_id = inp.idempotency_key or str(inp.correlation.correlation_id)
        task_queue = self._default_task_queue

        started_id = await self._helper.start(
            inp.procedure_type.value,
            inp.payload,
            workflow_id=workflow_id,
            task_queue=task_queue,
        )

        return ProcedureHandle(
            workflow_id=WorkflowId(started_id),
            procedure_type=inp.procedure_type,
            tenant_id=inp.tenant_id,
            correlation=inp.correlation,
            task_queue=task_queue,
        )

    async def get_status(
        self,
        tenant_id: "TenantId",
        workflow_id: "WorkflowId",
    ) -> "ProcedureResult":
        """Return current status of a workflow as a ProcedureResult.

        # implements WorkflowGatewayPort.get_status

        Args:
            tenant_id:   Tenant scope (used for audit; not passed to Temporal).
            workflow_id: Workflow identifier.

        Returns:
            ProcedureResult with status, output, and error fields populated.

        Raises:
            WorkflowNotFoundError: Workflow does not exist.
            TemporalRpcError: Any other Temporal error.
        """
        from dataspace_control_plane_core.procedure_runtime.contracts import (
            ProcedureResult,
            ProcedureStatus,
        )

        desc = await self._helper.describe(str(workflow_id))

        # Map Temporal status strings to core ProcedureStatus
        status_str = (desc.get("status") or "").upper()
        status = _map_temporal_status(status_str)

        return ProcedureResult(
            workflow_id=workflow_id,
            status=status,
            output={"run_id": desc.get("run_id"), "task_queue": desc.get("task_queue")},
        )

    async def cancel(
        self,
        tenant_id: "TenantId",
        workflow_id: "WorkflowId",
        reason: str,
    ) -> None:
        """Cancel a running workflow.

        # implements WorkflowGatewayPort.cancel

        Args:
            tenant_id:   Tenant scope (used for audit; not passed to Temporal).
            workflow_id: Workflow identifier.
            reason:      Human-readable cancellation reason.

        Raises:
            WorkflowNotFoundError: Workflow does not exist.
            TemporalRpcError: Any other Temporal error.
        """
        await self._helper.cancel(str(workflow_id))
        logger.info(
            "Workflow cancelled tenant=%s workflow_id=%s reason=%s",
            tenant_id, workflow_id, reason,
        )

    async def signal(
        self,
        tenant_id: "TenantId",
        workflow_id: "WorkflowId",
        signal: str,
        payload: dict[str, Any],
    ) -> None:
        """Send a signal to a running workflow.

        # implements WorkflowGatewayPort.signal

        Args:
            tenant_id:   Tenant scope (used for audit; not passed to Temporal).
            workflow_id: Workflow identifier.
            signal:      Signal name registered in the workflow definition.
            payload:     Signal payload dict.

        Raises:
            WorkflowNotFoundError: Workflow does not exist.
            TemporalRpcError: Any other Temporal error.
        """
        await self._signal_sender.send(str(workflow_id), signal, payload)


def _map_temporal_status(temporal_status: str) -> "ProcedureStatus":
    """Map a Temporal workflow status string to a core ProcedureStatus."""
    from dataspace_control_plane_core.procedure_runtime.contracts import ProcedureStatus

    mapping: dict[str, ProcedureStatus] = {
        "RUNNING": ProcedureStatus.RUNNING,
        "WORKFLOW_EXECUTION_STATUS_RUNNING": ProcedureStatus.RUNNING,
        "COMPLETED": ProcedureStatus.COMPLETED,
        "WORKFLOW_EXECUTION_STATUS_COMPLETED": ProcedureStatus.COMPLETED,
        "FAILED": ProcedureStatus.FAILED,
        "WORKFLOW_EXECUTION_STATUS_FAILED": ProcedureStatus.FAILED,
        "CANCELED": ProcedureStatus.CANCELLED,
        "WORKFLOW_EXECUTION_STATUS_CANCELED": ProcedureStatus.CANCELLED,
        "TIMED_OUT": ProcedureStatus.TIMED_OUT,
        "WORKFLOW_EXECUTION_STATUS_TIMED_OUT": ProcedureStatus.TIMED_OUT,
    }
    return mapping.get(temporal_status, ProcedureStatus.PENDING)
