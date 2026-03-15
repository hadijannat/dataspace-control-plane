"""Temporal signal helpers.

Provides typed wrappers for sending signals to running workflow executions.
Signals are one-way — no return value is expected.

Usage:
    sender = SignalSender(client)
    await sender.send("wf-001", "approval-received", payload={"approved": True})
"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from .errors import TemporalRpcError, WorkflowNotFoundError

if TYPE_CHECKING:
    import temporalio.client

logger = logging.getLogger(__name__)


class SignalSender:
    """Sends signals to Temporal workflow executions.

    All signals are fire-and-forget from the caller's perspective; Temporal
    guarantees delivery to the workflow once the RPC completes.
    """

    def __init__(self, client: "temporalio.client.Client") -> None:
        self._client = client

    async def send(
        self,
        workflow_id: str,
        signal_name: str,
        payload: Any = None,
        *,
        run_id: str | None = None,
    ) -> None:
        """Send a named signal to a running workflow.

        Args:
            workflow_id:  Target workflow identifier.
            signal_name:  Signal name registered in the workflow definition.
            payload:      Optional serialisable signal argument (default: None).
            run_id:       Optional run ID to target a specific workflow run.

        Raises:
            WorkflowNotFoundError: The workflow does not exist or is not running.
            TemporalRpcError:      Any other Temporal RPC error.
        """
        try:
            handle = self._client.get_workflow_handle(workflow_id, run_id=run_id)
            if payload is None:
                await handle.signal(signal_name)
            else:
                await handle.signal(signal_name, payload)
            logger.debug(
                "Sent signal %s to workflow id=%s", signal_name, workflow_id
            )
        except Exception as exc:
            exc_str = str(exc).lower()
            if "not found" in exc_str:
                raise WorkflowNotFoundError(workflow_id, run_id) from exc
            raise TemporalRpcError(
                f"Failed to send signal {signal_name!r} to workflow id={workflow_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc
