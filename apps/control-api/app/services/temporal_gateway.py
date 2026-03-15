"""
Temporal gateway: thin facade over the Temporal client.
All workflow interaction from route handlers goes through here.

Routing table
-------------
``PROCEDURE_TYPE_TO_TASK_QUEUE`` maps logical procedure type names to the
Temporal task queue that hosts the corresponding worker. Adding a new
procedure type requires only a new entry here plus a matching worker
registration in ``apps/temporal-workers``.
"""
import uuid
from typing import Any

import structlog
from temporalio.client import Client, WorkflowExecutionDescription, WorkflowHandle

from app.application.commands.procedures import StartProcedureCommand
from app.services.procedure_catalog import ProcedureCatalog, ProcedureDefinition

logger = structlog.get_logger(__name__)


class TemporalGateway:
    def __init__(self, client: Client) -> None:
        self._client = client

    async def start_procedure(
        self,
        command: StartProcedureCommand,
        catalog: ProcedureCatalog,
    ) -> WorkflowHandle:
        """
        Dispatch a ``StartProcedureCommand`` to the appropriate Temporal task queue.

        The task queue is resolved from ``PROCEDURE_TYPE_TO_TASK_QUEUE``. A
        ``ValueError`` is raised for unknown procedure types so callers can
        return HTTP 422 rather than silently enqueuing to a non-existent queue.

        The workflow_id is taken from ``command.idempotency_key`` when present;
        otherwise a deterministic ``<procedure_type>-<tenant_id>-<uuid4>``
        string is generated. Using the idempotency key as the workflow_id gives
        Temporal's built-in deduplication for free.

        Parameters
        ----------
        command:
            Fully populated ``StartProcedureCommand`` from the route handler.

        Returns
        -------
        WorkflowHandle
            Handle to the newly started (or already-running) workflow.

        Raises
        ------
        ValueError
            If ``command.procedure_type`` is not in ``PROCEDURE_TYPE_TO_TASK_QUEUE``.
        """
        definition = catalog.resolve(command.procedure_type)
        workflow_input = catalog.build_workflow_input(
            definition,
            tenant_id=command.tenant_id,
            legal_entity_id=command.legal_entity_id,
            payload=command.payload,
            idempotency_key=command.idempotency_key,
        )
        workflow_id = catalog.build_workflow_id(definition, workflow_input)
        search_attributes = catalog.build_search_attributes(definition, workflow_input)
        id_conflict_policy, id_reuse_policy = catalog.build_conflict_policy(definition)

        logger.info(
            "temporal.start_procedure",
            workflow_id=workflow_id,
            procedure_type=command.procedure_type,
            tenant_id=command.tenant_id,
            workflow_type=definition.workflow_type,
            task_queue=definition.task_queue,
            actor=command.actor_subject,
        )

        handle = await self._client.start_workflow(
            definition.workflow_type,
            workflow_input,
            id=workflow_id,
            task_queue=definition.task_queue,
            search_attributes=search_attributes,
            id_conflict_policy=id_conflict_policy,
            id_reuse_policy=id_reuse_policy,
        )
        return handle

    async def start_workflow(
        self,
        workflow_type: str,
        task_queue: str,
        args: dict[str, Any],
        workflow_id: str | None = None,
        search_attributes: dict[str, Any] | None = None,
    ) -> WorkflowHandle:
        """
        Low-level workflow start. Prefer ``start_procedure`` for procedure dispatch.

        Parameters
        ----------
        workflow_type:
            Temporal workflow type name (registered workflow class name).
        task_queue:
            Target task queue.
        args:
            Workflow input arguments forwarded verbatim.
        workflow_id:
            Explicit workflow ID; a UUID-based default is used when omitted.
        search_attributes:
            Optional Temporal search attributes (reserved for future use).
        """
        wid = workflow_id or f"{workflow_type}-{uuid.uuid4()}"
        logger.info(
            "temporal.start_workflow",
            workflow_id=wid,
            workflow_type=workflow_type,
            task_queue=task_queue,
        )
        handle = await self._client.start_workflow(
            workflow_type,
            args,
            id=wid,
            task_queue=task_queue,
        )
        return handle

    async def signal_workflow(self, workflow_id: str, signal_name: str, payload: Any = None) -> None:
        handle = self._client.get_workflow_handle(workflow_id)
        await handle.signal(signal_name, payload)

    async def query_workflow(self, workflow_id: str, query_name: str) -> Any:
        handle = self._client.get_workflow_handle(workflow_id)
        return await handle.query(query_name)

    async def describe_workflow(self, workflow_id: str) -> WorkflowExecutionDescription:
        handle = self._client.get_workflow_handle(workflow_id)
        return await handle.describe()
