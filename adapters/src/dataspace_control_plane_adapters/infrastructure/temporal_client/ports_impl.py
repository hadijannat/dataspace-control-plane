"""Temporal WorkflowGatewayPort implementation.

Implements core/procedure_runtime/ports.py WorkflowGatewayPort using the
temporalio.client.Client wrapper helpers in this package.

This module is the authoritative wiring point between the core port contract
and the Temporal SDK. Apps/temporal-workers inject TemporalWorkflowGateway
into procedure services via dependency injection at container startup.
"""
from __future__ import annotations

import logging
from dataclasses import asdict, is_dataclass
from datetime import datetime
from typing import Any, Mapping, TYPE_CHECKING

from dataspace_control_plane_core.domains._shared.actor import ActorRef, ActorType
from dataspace_control_plane_core.procedure_runtime.messages import (
    ApproveProcedure,
    CancelProcedure,
    PauseProcedure,
    ProcedureQuery,
    ProcedureQueryResponse,
    RejectProcedure,
    ResumeProcedure,
    RetryProcedure,
)

if TYPE_CHECKING:
    import temporalio.client
    # Use the canonical workflow_contracts module; contracts.py is a deprecated facade.
    from dataspace_control_plane_core.procedure_runtime.workflow_contracts import (
        ProcedureHandle,
        ProcedureInput,
        ProcedureResult,
        ProcedureStatus,
    )
    from dataspace_control_plane_core.domains._shared.ids import TenantId, WorkflowId

from .errors import TemporalRpcError, WorkflowNotFoundError
from .queries import QueryExecutor
from .signals import SignalSender
from .updates import UpdateExecutor
from .workflow_handles import WorkflowHandleHelper

logger = logging.getLogger(__name__)

_DEFAULT_CONTROL_NAMES: dict[str, str] = {
    "approve": "approve",
    "reject": "reject",
    "pause": "pause",
    "resume": "resume",
    "retry": "retry",
    "query": "get_status",
}

_WORKFLOW_TYPE_TO_PROCEDURE_TYPE: dict[str, str] = {
    "CompanyOnboardingWorkflow": "company-onboarding",
    "ConnectorBootstrapWorkflow": "connector-bootstrap",
    "RotateCredentialsWorkflow": "machine-credential-rotation",
    "WalletBootstrapWorkflow": "machine-credential-rotation",
    "RevokeCredentialsWorkflow": "machine-credential-rotation",
    "PublishAssetWorkflow": "asset-twin-publication",
    "RegisterDigitalTwinWorkflow": "asset-twin-publication",
    "DppProvisionWorkflow": "asset-twin-publication",
    "NegotiateContractWorkflow": "contract-negotiation",
    "EvidenceExportWorkflow": "compliance-gap-scan",
}


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
        control_names: Mapping[str, str] | None = None,
    ) -> None:
        self._helper = WorkflowHandleHelper(client)
        self._signal_sender = SignalSender(client)
        self._query_executor = QueryExecutor(client)
        self._update_executor = UpdateExecutor(client)
        self._default_task_queue = default_task_queue
        self._control_names = dict(_DEFAULT_CONTROL_NAMES)
        if control_names:
            self._control_names.update(control_names)

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

        # Namespace workflow IDs by tenant to prevent cross-tenant collisions in
        # a shared Temporal namespace.  Callers that already embed the tenant
        # prefix (e.g. "{tenant_id}:{procedure_prefix}:{id}") are not re-prefixed.
        tenant_prefix = f"{inp.tenant_id}:"
        raw_id = inp.idempotency_key or str(inp.correlation.correlation_id)
        workflow_id = raw_id if raw_id.startswith(tenant_prefix) else f"{tenant_prefix}{raw_id}"
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
        from dataspace_control_plane_core.procedure_runtime.workflow_contracts import (
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
        message: CancelProcedure,
    ) -> None:
        """Cancel a running workflow."""
        await self._helper.cancel(str(message.workflow_id))
        logger.info(
            "Workflow cancelled tenant=%s workflow_id=%s reason=%s",
            message.tenant_id,
            message.workflow_id,
            message.reason,
        )

    async def approve(self, message: ApproveProcedure) -> None:
        await self._send_control_update(
            str(message.workflow_id),
            "approve",
            {
                "reviewer_id": message.actor.subject,
                "notes": message.comment,
            },
        )

    async def reject(self, message: RejectProcedure) -> None:
        await self._send_control_update(
            str(message.workflow_id),
            "reject",
            {
                "reviewer_id": message.actor.subject,
                "reason": message.reason,
            },
        )

    async def pause(self, message: PauseProcedure) -> None:
        await self._send_control_update(
            str(message.workflow_id),
            "pause",
            {
                "reviewer_id": message.actor.subject,
                "reason": message.reason,
            },
        )

    async def resume(self, message: ResumeProcedure) -> None:
        await self._send_control_update(
            str(message.workflow_id),
            "resume",
            {
                "reviewer_id": message.actor.subject,
                "notes": message.reason,
            },
        )

    async def retry(self, message: RetryProcedure) -> None:
        await self._send_control_update(
            str(message.workflow_id),
            "retry",
            {
                "actor_id": message.actor.subject,
                "reason": message.reason,
            },
        )

    async def signal(
        self,
        tenant_id: "TenantId",
        workflow_id: "WorkflowId",
        signal: str,
        payload: dict[str, Any],
    ) -> None:
        """Send a signal to a running workflow."""
        await self._signal_sender.send(str(workflow_id), signal, payload)

    async def query(self, message: ProcedureQuery) -> ProcedureQueryResponse:
        """Return a best-effort ``ProcedureQueryResponse`` for the target workflow."""
        raw_query = await self._query_executor.execute(
            str(message.workflow_id),
            self._control_names["query"],
        )
        desc = await self._helper.describe(str(message.workflow_id))
        normalized_query = _normalize_query_result(raw_query)

        from dataspace_control_plane_core.procedure_runtime.procedure_ids import (
            ProcedureHandle,
            ProcedureType,
        )
        from dataspace_control_plane_core.procedure_runtime.workflow_contracts import (
            ManualReviewState,
            ProcedureInput,
            ProcedureResult,
            ProcedureSnapshot,
            ProcedureState,
            ProcedureStatus,
        )

        procedure_type = ProcedureType(
            _infer_procedure_type(desc.get("workflow_type"), str(message.workflow_id))
        )
        status = _resolve_status((desc.get("status") or "").upper(), normalized_query)
        handle = ProcedureHandle(
            workflow_id=message.workflow_id,
            procedure_type=procedure_type,
            tenant_id=message.tenant_id,
            correlation=message.correlation,
            run_id=str(desc.get("run_id") or ""),
            task_queue=str(desc.get("task_queue") or self._default_task_queue),
        )
        state = ProcedureState(
            status=status,
            manual_review=_manual_review_state_from_query(normalized_query),
            message=_message_from_query(normalized_query),
        )
        procedure_input = ProcedureInput(
            tenant_id=message.tenant_id,
            procedure_type=procedure_type,
            actor=ActorRef(
                subject="temporal-client",
                actor_type=ActorType.SERVICE,
                tenant_id=message.tenant_id,
                display_name="Temporal client adapter",
            ),
            correlation=message.correlation,
            payload=_query_payload(normalized_query, message.include_payload),
            idempotency_key=str(message.workflow_id),
        )
        result = ProcedureResult(
            workflow_id=message.workflow_id,
            status=status,
            output=_query_output(normalized_query, desc),
            completed_at=_parse_iso_datetime(desc.get("close_time")),
        ) if status in {
            ProcedureStatus.COMPLETED,
            ProcedureStatus.FAILED,
            ProcedureStatus.CANCELLED,
            ProcedureStatus.TIMED_OUT,
        } else None

        snapshot = ProcedureSnapshot(
            handle=handle,
            state=state,
            input=procedure_input,
            result=result,
        )
        return ProcedureQueryResponse(
            snapshot=snapshot,
            metadata={
                "query_name": self._control_names["query"],
                "workflow_type": desc.get("workflow_type"),
            },
        )

    async def _send_control_update(
        self,
        workflow_id: str,
        action: str,
        payload: dict[str, Any],
    ) -> None:
        update_name = self._control_names[action]
        await self._update_executor.send(workflow_id, update_name, payload)


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


def _resolve_status(
    temporal_status: str,
    raw_query: Any,
) -> "ProcedureStatus":
    """Refine Temporal's coarse execution status with workflow query details."""
    from dataspace_control_plane_core.procedure_runtime.contracts import ProcedureStatus

    status = _map_temporal_status(temporal_status)
    if status is not ProcedureStatus.RUNNING or not isinstance(raw_query, dict):
        return status

    if bool(raw_query.get("is_paused")):
        return ProcedureStatus.PAUSED

    manual_review = raw_query.get("manual_review")
    if isinstance(manual_review, dict):
        if bool(manual_review.get("is_pending")):
            return ProcedureStatus.WAITING_FOR_APPROVAL
        decision = str(manual_review.get("decision") or "").casefold()
        if decision == "rejected":
            return ProcedureStatus.FAILED

    next_action = str(
        raw_query.get("next_required_action")
        or raw_query.get("next_action")
        or ""
    ).casefold()
    blocking_reason = str(raw_query.get("blocking_reason") or "").strip()
    if next_action in {"approve", "reject", "resume", "force_republish"} or blocking_reason:
        return ProcedureStatus.WAITING_FOR_APPROVAL

    return status


def _infer_procedure_type(workflow_type: str | None, workflow_id: str) -> str:
    """Map runtime workflow identities into the current core ProcedureType set.

    Multiple concrete procedures currently collapse into the nearest available
    core runtime category. This keeps the adapter aligned with the current
    core contract without inventing new core semantics in adapters/.

    Workflow IDs are now tenant-prefixed ("{tenant_id}:{procedure_prefix}:…").
    The prefix map is checked against both the full ID and the ID with the
    first colon-delimited segment stripped so that existing callers using
    bare procedure-prefixed IDs continue to resolve correctly.
    """

    if workflow_type and workflow_type in _WORKFLOW_TYPE_TO_PROCEDURE_TYPE:
        return _WORKFLOW_TYPE_TO_PROCEDURE_TYPE[workflow_type]

    # Derive a bare ID by stripping the optional tenant prefix segment.
    _colon = workflow_id.find(":")
    bare_id = workflow_id[_colon + 1:] if _colon != -1 else workflow_id

    prefix_map = {
        "company-onboarding:": "company-onboarding",
        "connector:": "connector-bootstrap",
        "contract:": "contract-negotiation",
        "rotate-credentials:": "machine-credential-rotation",
        "wallet:": "machine-credential-rotation",
        "revoke-credentials:": "machine-credential-rotation",
        "publish-asset:": "asset-twin-publication",
        "register-twin:": "asset-twin-publication",
        "dpp:": "asset-twin-publication",
        "evidence-export:": "compliance-gap-scan",
    }
    for prefix, procedure_type in prefix_map.items():
        if bare_id.startswith(prefix) or workflow_id.startswith(prefix):
            return procedure_type

    raise TemporalRpcError(
        f"Cannot infer ProcedureType for workflow id={workflow_id!r} workflow_type={workflow_type!r}. "
        "The adapter needs either a normalized runtime control convention or a broader core ProcedureType set.",
        upstream_code="unknown_workflow_type",
    )


def _manual_review_state_from_query(raw_query: Any) -> "ManualReviewState":
    from dataspace_control_plane_core.procedure_runtime.workflow_contracts import (
        ManualReviewState,
    )

    if isinstance(raw_query, dict):
        manual_review = raw_query.get("manual_review")
        if isinstance(manual_review, dict):
            if bool(manual_review.get("is_pending")):
                return ManualReviewState.PENDING
            decision = str(manual_review.get("decision") or "").casefold()
            if decision == "approved":
                return ManualReviewState.APPROVED
            if decision == "rejected":
                return ManualReviewState.REJECTED
        blocking_reason = str(raw_query.get("blocking_reason") or raw_query.get("next_action") or "")
        if blocking_reason:
            return ManualReviewState.PENDING
    return ManualReviewState.NOT_REQUIRED


def _message_from_query(raw_query: Any) -> str:
    if isinstance(raw_query, dict):
        for key in (
            "message",
            "phase",
            "state",
            "negotiation_state",
            "wallet_state",
            "rotation_state",
            "next_required_action",
        ):
            value = raw_query.get(key)
            if value:
                return str(value)
    return ""


def _query_payload(raw_query: Any, include_payload: bool) -> dict[str, Any]:
    if include_payload and isinstance(raw_query, dict):
        return dict(raw_query)
    return {}


def _query_output(raw_query: Any, description: dict[str, Any]) -> dict[str, Any]:
    output = {
        "run_id": description.get("run_id"),
        "task_queue": description.get("task_queue"),
    }
    if isinstance(raw_query, dict):
        output["status_query"] = dict(raw_query)
    elif raw_query is not None:
        output["status_query"] = raw_query
    return output


def _normalize_query_result(raw_query: Any) -> Any:
    if isinstance(raw_query, dict):
        return dict(raw_query)
    if is_dataclass(raw_query):
        return asdict(raw_query)
    model_dump = getattr(raw_query, "model_dump", None)
    if callable(model_dump):
        return model_dump()
    return raw_query


def _parse_iso_datetime(raw: Any) -> datetime | None:
    if not raw:
        return None
    try:
        return datetime.fromisoformat(str(raw))
    except ValueError:
        return None
