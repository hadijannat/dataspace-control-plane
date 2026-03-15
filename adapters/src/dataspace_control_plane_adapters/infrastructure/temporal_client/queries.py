"""Temporal query helpers.

Provides typed wrappers for executing synchronous queries against running
or completed workflow executions.

Usage:
    executor = QueryExecutor(client)
    result = await executor.execute("wf-001", "get-status")
"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from .errors import TemporalRpcError, WorkflowNotFoundError

if TYPE_CHECKING:
    import temporalio.client

logger = logging.getLogger(__name__)


class QueryExecutor:
    """Executes synchronous queries against Temporal workflow executions.

    Queries are handled by the workflow's query handler in a deterministic,
    read-only fashion. They do not advance the workflow's event history.
    """

    def __init__(self, client: "temporalio.client.Client") -> None:
        self._client = client

    async def execute(
        self,
        workflow_id: str,
        query_name: str,
        input: Any = None,
        *,
        run_id: str | None = None,
    ) -> Any:
        """Execute a named query on a workflow.

        Args:
            workflow_id: Target workflow identifier.
            query_name:  Query handler name registered in the workflow definition.
            input:       Optional serialisable query argument (default: None).
            run_id:      Optional run ID to target a specific workflow run.

        Returns:
            Deserialized query result as returned by the workflow's query handler.

        Raises:
            WorkflowNotFoundError: The workflow does not exist.
            TemporalRpcError:      Any other Temporal RPC error.
        """
        try:
            handle = self._client.get_workflow_handle(workflow_id, run_id=run_id)
            if input is None:
                result = await handle.query(query_name)
            else:
                result = await handle.query(query_name, input)
            logger.debug(
                "Executed query %s on workflow id=%s", query_name, workflow_id
            )
            return result
        except Exception as exc:
            exc_str = str(exc).lower()
            if "not found" in exc_str:
                raise WorkflowNotFoundError(workflow_id, run_id) from exc
            raise TemporalRpcError(
                f"Failed to execute query {query_name!r} on workflow id={workflow_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc
