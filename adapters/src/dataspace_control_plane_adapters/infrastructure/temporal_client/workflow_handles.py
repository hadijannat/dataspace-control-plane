"""Temporal workflow lifecycle helpers.

Provides typed, high-level wrappers around the temporalio.client.Client API
for starting, querying, and terminating workflows.

Usage:
    helper = WorkflowHandleHelper(client)
    wf_id = await helper.start("MyWorkflow", input_data, workflow_id="wf-001", task_queue="q")
"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from .errors import (
    TemporalAdapterError,
    TemporalRpcError,
    WorkflowAlreadyStartedError,
    WorkflowNotFoundError,
)

if TYPE_CHECKING:
    import temporalio.client

logger = logging.getLogger(__name__)


class WorkflowHandleHelper:
    """High-level typed wrapper for Temporal workflow lifecycle operations.

    All operations map 1-to-1 to temporalio.client.Client APIs. Error types
    from the Temporal SDK are translated to adapter-layer errors so callers
    never see SDK-specific exception types.
    """

    def __init__(self, client: "temporalio.client.Client") -> None:
        self._client = client

    async def start(
        self,
        workflow_type: str,
        input: Any,
        *,
        workflow_id: str,
        task_queue: str,
        execution_timeout_s: float | None = None,
        run_timeout_s: float | None = None,
        task_timeout_s: float | None = None,
        id_reuse_policy: str = "REJECT_DUPLICATE",
    ) -> str:
        """Start a new workflow execution.

        Args:
            workflow_type:       Temporal workflow type name (string registration key).
            input:               Serialisable workflow input payload.
            workflow_id:         Unique workflow identifier.
            task_queue:          Task queue the worker must be listening on.
            execution_timeout_s: Optional total execution timeout in seconds.
            run_timeout_s:       Optional single run timeout in seconds.
            task_timeout_s:      Optional single task timeout in seconds.
            id_reuse_policy:     How to handle a duplicate workflow_id
                                 (REJECT_DUPLICATE, ALLOW_DUPLICATE, etc.).

        Returns:
            workflow_id of the started execution (same as the input workflow_id).

        Raises:
            WorkflowAlreadyStartedError: A workflow with workflow_id is already running.
            TemporalRpcError: Any other Temporal RPC error.
        """
        # Heavy SDK import deferred to avoid mandatory dependency at module load time.
        import temporalio.client
        import temporalio.common
        from temporalio.service import RPCError  # type: ignore[import]

        try:
            from datetime import timedelta

            start_kwargs: dict[str, Any] = {
                "id": workflow_id,
                "task_queue": task_queue,
            }
            if execution_timeout_s is not None:
                start_kwargs["execution_timeout"] = timedelta(seconds=execution_timeout_s)
            if run_timeout_s is not None:
                start_kwargs["run_timeout"] = timedelta(seconds=run_timeout_s)
            if task_timeout_s is not None:
                start_kwargs["task_timeout"] = timedelta(seconds=task_timeout_s)

            # Map string policy to SDK enum
            policy_map = {
                "REJECT_DUPLICATE": temporalio.common.WorkflowIDReusePolicy.REJECT_DUPLICATE,
                "ALLOW_DUPLICATE": temporalio.common.WorkflowIDReusePolicy.ALLOW_DUPLICATE,
                "ALLOW_DUPLICATE_FAILED_ONLY": temporalio.common.WorkflowIDReusePolicy.ALLOW_DUPLICATE_FAILED_ONLY,
                "TERMINATE_IF_RUNNING": temporalio.common.WorkflowIDReusePolicy.TERMINATE_IF_RUNNING,
            }
            start_kwargs["id_reuse_policy"] = policy_map.get(
                id_reuse_policy,
                temporalio.common.WorkflowIDReusePolicy.REJECT_DUPLICATE,
            )

            handle = await self._client.start_workflow(
                workflow_type,
                input,
                **start_kwargs,
            )
            logger.info(
                "Started workflow type=%s id=%s run_id=%s",
                workflow_type, workflow_id, handle.first_execution_run_id,
            )
            return handle.id

        except Exception as exc:
            exc_type_name = type(exc).__name__
            if "already" in str(exc).lower() or "already_exists" in exc_type_name.lower():
                raise WorkflowAlreadyStartedError(workflow_id) from exc
            raise TemporalRpcError(
                f"Failed to start workflow type={workflow_type!r} id={workflow_id!r}: {exc}",
                upstream_code=exc_type_name,
            ) from exc

    async def get_result(self, workflow_id: str, run_id: str | None = None) -> Any:
        """Await the result of a workflow execution.

        Args:
            workflow_id: Workflow identifier.
            run_id:      Optional run ID to address a specific run.

        Returns:
            Deserialized workflow result.

        Raises:
            WorkflowNotFoundError: No workflow with workflow_id exists.
            TemporalRpcError: Any other Temporal RPC error.
        """
        try:
            handle = self._client.get_workflow_handle(workflow_id, run_id=run_id)
            return await handle.result()
        except Exception as exc:
            exc_str = str(exc).lower()
            if "not found" in exc_str or "does_not_exist" in exc_str:
                raise WorkflowNotFoundError(workflow_id, run_id) from exc
            raise TemporalRpcError(
                f"Failed to get result for workflow id={workflow_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc

    async def terminate(self, workflow_id: str, reason: str) -> None:
        """Terminate a running workflow.

        Args:
            workflow_id: Workflow identifier.
            reason:      Human-readable termination reason (logged by Temporal).

        Raises:
            WorkflowNotFoundError: No workflow with workflow_id exists.
            TemporalRpcError: Any other Temporal RPC error.
        """
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            await handle.terminate(reason=reason)
            logger.info("Terminated workflow id=%s reason=%s", workflow_id, reason)
        except Exception as exc:
            exc_str = str(exc).lower()
            if "not found" in exc_str:
                raise WorkflowNotFoundError(workflow_id) from exc
            raise TemporalRpcError(
                f"Failed to terminate workflow id={workflow_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc

    async def cancel(self, workflow_id: str) -> None:
        """Request cancellation of a running workflow.

        Args:
            workflow_id: Workflow identifier.

        Raises:
            WorkflowNotFoundError: No workflow with workflow_id exists.
            TemporalRpcError: Any other Temporal RPC error.
        """
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            await handle.cancel()
            logger.info("Cancelled workflow id=%s", workflow_id)
        except Exception as exc:
            exc_str = str(exc).lower()
            if "not found" in exc_str:
                raise WorkflowNotFoundError(workflow_id) from exc
            raise TemporalRpcError(
                f"Failed to cancel workflow id={workflow_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc

    async def describe(self, workflow_id: str) -> dict[str, Any]:
        """Return metadata about a workflow execution.

        Args:
            workflow_id: Workflow identifier.

        Returns:
            Dictionary with status, run_id, workflow_type, start_time, close_time.

        Raises:
            WorkflowNotFoundError: No workflow with workflow_id exists.
            TemporalRpcError: Any other Temporal RPC error.
        """
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            desc = await handle.describe()
            return {
                "workflow_id": desc.id,
                "run_id": desc.run_id,
                "workflow_type": desc.workflow_type,
                "status": str(desc.status),
                "start_time": desc.start_time.isoformat() if desc.start_time else None,
                "close_time": desc.close_time.isoformat() if desc.close_time else None,
                "task_queue": desc.task_queue,
            }
        except Exception as exc:
            exc_str = str(exc).lower()
            if "not found" in exc_str:
                raise WorkflowNotFoundError(workflow_id) from exc
            raise TemporalRpcError(
                f"Failed to describe workflow id={workflow_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc
