"""Temporal update helpers.

Provides typed wrappers for sending durable updates to running workflow
executions. Unlike signals, updates have return values and can be rejected
by a workflow-defined validator.

Usage:
    executor = UpdateExecutor(client)
    result = await executor.send_and_wait("wf-001", "approve-step", {"step_id": "step-3"})
"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from .errors import TemporalRpcError, WorkflowNotFoundError

if TYPE_CHECKING:
    import temporalio.client

logger = logging.getLogger(__name__)


class UpdateExecutor:
    """Sends durable updates to Temporal workflow executions.

    Updates are durably recorded in the workflow history and can be
    acknowledged, rejected, or responded to by the workflow handler.
    """

    def __init__(self, client: "temporalio.client.Client") -> None:
        self._client = client

    async def send(
        self,
        workflow_id: str,
        update_name: str,
        input: Any,
        *,
        run_id: str | None = None,
        update_id: str | None = None,
    ) -> Any:
        """Send a named update and wait for it to be accepted.

        Args:
            workflow_id: Target workflow identifier.
            update_name: Update handler name registered in the workflow definition.
            input:       Serialisable update argument.
            run_id:      Optional run ID to target a specific workflow run.
            update_id:   Optional idempotency key for the update request.

        Returns:
            Update result returned by the workflow's update handler.

        Raises:
            WorkflowNotFoundError: The workflow does not exist.
            TemporalRpcError:      Any other Temporal RPC error.
        """
        # TODO: production impl — wire update_id for idempotent re-sends once
        # the temporalio SDK stabilises the UpdateHandle API.
        from datetime import timedelta
        try:
            handle = self._client.get_workflow_handle(workflow_id, run_id=run_id)
            result = await handle.execute_update(update_name, input)
            logger.debug(
                "Sent update %s to workflow id=%s", update_name, workflow_id
            )
            return result
        except Exception as exc:
            exc_str = str(exc).lower()
            if "not found" in exc_str:
                raise WorkflowNotFoundError(workflow_id, run_id) from exc
            raise TemporalRpcError(
                f"Failed to send update {update_name!r} to workflow id={workflow_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc

    async def send_and_wait(
        self,
        workflow_id: str,
        update_name: str,
        input: Any,
        *,
        run_id: str | None = None,
        timeout_s: float = 30.0,
        update_id: str | None = None,
    ) -> Any:
        """Send a named update and wait up to *timeout_s* seconds for the result.

        This is a convenience wrapper around ``send`` that adds a deadline.

        Args:
            workflow_id: Target workflow identifier.
            update_name: Update handler name.
            input:       Serialisable update argument.
            run_id:      Optional run ID.
            timeout_s:   Maximum seconds to wait for the update result (default: 30).
            update_id:   Optional idempotency key.

        Returns:
            Update result returned by the workflow's update handler.

        Raises:
            WorkflowNotFoundError: The workflow does not exist.
            TemporalRpcError:      RPC error or timeout exceeded.
        """
        import asyncio

        try:
            return await asyncio.wait_for(
                self.send(
                    workflow_id,
                    update_name,
                    input,
                    run_id=run_id,
                    update_id=update_id,
                ),
                timeout=timeout_s,
            )
        except asyncio.TimeoutError as exc:
            raise TemporalRpcError(
                f"Update {update_name!r} on workflow id={workflow_id!r} timed out after {timeout_s}s",
                upstream_code="timeout",
            ) from exc
