"""Temporal gateway: thin facade over the Temporal client."""
import uuid
from dataclasses import dataclass
from typing import Any

import structlog
from dataspace_control_plane_adapters.infrastructure.temporal_client.errors import (
    TemporalRpcError,
    WorkflowAlreadyStartedError,
    WorkflowNotFoundError,
)
from temporalio.client import Client, WorkflowExecutionDescription
from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy

from app.application.commands.procedures import StartProcedureCommand
from app.services.procedure_catalog import ProcedureCatalog, ProcedureDefinition

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class StartedWorkflow:
    workflow_id: str
    run_id: str | None = None


class TemporalGateway:
    def __init__(self, client: Client) -> None:
        self._client = client

    async def start_procedure(
        self,
        command: StartProcedureCommand,
        catalog: ProcedureCatalog,
    ) -> StartedWorkflow:
        """Dispatch a validated start command through the manifest-backed catalog."""
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

        return await self.start_definition(
            definition=definition,
            workflow_input=workflow_input,
            workflow_id=workflow_id,
            search_attributes=search_attributes,
            id_conflict_policy=id_conflict_policy,
            id_reuse_policy=id_reuse_policy,
        )

    async def start_definition(
        self,
        *,
        definition: ProcedureDefinition,
        workflow_input: Any,
        workflow_id: str,
        search_attributes: dict[str, list[str]],
        id_conflict_policy=None,
        id_reuse_policy=None,
    ) -> StartedWorkflow:
        if id_conflict_policy is None or id_reuse_policy is None:
            id_conflict_policy, id_reuse_policy = self._client_conflict_policy(definition)

        try:
            handle = await self._client.start_workflow(
                definition.workflow_type,
                workflow_input,
                id=workflow_id,
                task_queue=definition.task_queue,
                search_attributes=search_attributes,
                id_conflict_policy=id_conflict_policy,
                id_reuse_policy=id_reuse_policy,
            )
            return StartedWorkflow(
                workflow_id=handle.id,
                run_id=getattr(handle, "first_execution_run_id", None),
            )
        except Exception as exc:
            message = str(exc).lower()
            if "already" in message and "workflow" in message:
                raise WorkflowAlreadyStartedError(workflow_id) from exc
            raise TemporalRpcError(
                f"Failed to start workflow id={workflow_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc

    def _client_conflict_policy(
        self,
        definition: ProcedureDefinition,
    ) -> tuple[WorkflowIDConflictPolicy, WorkflowIDReusePolicy]:
        conflict_policy = definition.manifest.conflict_policy
        if conflict_policy == "use_existing":
            return (
                WorkflowIDConflictPolicy.USE_EXISTING,
                WorkflowIDReusePolicy.REJECT_DUPLICATE,
            )
        if conflict_policy == "reject":
            return (
                WorkflowIDConflictPolicy.FAIL,
                WorkflowIDReusePolicy.REJECT_DUPLICATE,
            )
        return (
            WorkflowIDConflictPolicy.UNSPECIFIED,
            WorkflowIDReusePolicy.ALLOW_DUPLICATE,
        )

    async def start_workflow(
        self,
        workflow_type: str,
        task_queue: str,
        args: dict[str, Any],
        workflow_id: str | None = None,
        search_attributes: dict[str, Any] | None = None,
    ) -> StartedWorkflow:
        """Low-level workflow start. Prefer ``start_procedure`` for procedure dispatch."""
        wid = workflow_id or f"{workflow_type}-{uuid.uuid4()}"
        logger.info(
            "temporal.start_workflow",
            workflow_id=wid,
            workflow_type=workflow_type,
            task_queue=task_queue,
        )
        try:
            handle = await self._client.start_workflow(
                workflow_type,
                args,
                id=wid,
                task_queue=task_queue,
            )
            return StartedWorkflow(
                workflow_id=handle.id,
                run_id=getattr(handle, "first_execution_run_id", None),
            )
        except Exception as exc:
            message = str(exc).lower()
            if "already" in message and "workflow" in message:
                raise WorkflowAlreadyStartedError(wid) from exc
            raise TemporalRpcError(
                f"Failed to start workflow id={wid!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc

    async def get_result(self, workflow_id: str) -> Any:
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            return await handle.result()
        except Exception as exc:
            if "not found" in str(exc).lower():
                raise WorkflowNotFoundError(workflow_id) from exc
            raise TemporalRpcError(
                f"Failed to fetch workflow result id={workflow_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc

    async def signal_workflow(self, workflow_id: str, signal_name: str, payload: Any = None) -> None:
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            await handle.signal(signal_name, payload)
        except Exception as exc:
            if "not found" in str(exc).lower():
                raise WorkflowNotFoundError(workflow_id) from exc
            raise TemporalRpcError(
                f"Failed to signal workflow id={workflow_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc

    async def query_workflow(self, workflow_id: str, query_name: str) -> Any:
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            return await handle.query(query_name)
        except Exception as exc:
            if "not found" in str(exc).lower():
                raise WorkflowNotFoundError(workflow_id) from exc
            raise TemporalRpcError(
                f"Failed to query workflow id={workflow_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc

    async def describe_workflow(self, workflow_id: str) -> WorkflowExecutionDescription:
        try:
            handle = self._client.get_workflow_handle(workflow_id)
            return await handle.describe()
        except Exception as exc:
            if "not found" in str(exc).lower():
                raise WorkflowNotFoundError(workflow_id) from exc
            raise TemporalRpcError(
                f"Failed to describe workflow id={workflow_id!r}: {exc}",
                upstream_code=type(exc).__name__,
            ) from exc
