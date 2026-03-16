from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Any

import structlog
from dataspace_control_plane_adapters.infrastructure.temporal_client.errors import (
    TemporalRpcError,
    WorkflowNotFoundError,
)
from dataspace_control_plane_core.procedure_runtime.api import ProcedureRuntimeState
from dataspace_control_plane_core.domains._shared.time import utc_now

from app.application.dto.procedures import ProcedureStatusDTO
from app.services import read_models
from app.services.procedure_catalog import ProcedureCatalog
from app.services.temporal_gateway import TemporalGateway

logger = structlog.get_logger(__name__)

_STATUS_MAP = {
    "canceled": "cancelled",
    "cancelled": "cancelled",
    "completed": "completed",
    "failed": "failed",
    "pending": "pending",
    "paused": "paused",
    "running": "running",
    "terminated": "cancelled",
    "timed_out": "timed_out",
    "timed-out": "timed_out",
    "waiting_for_approval": "waiting_for_approval",
}
_TERMINAL_STATUSES = {"completed", "failed", "cancelled", "timed_out"}


def _normalize_status(raw_status: str | None) -> str:
    if raw_status is None:
        return "running"
    normalized = raw_status.strip().lower()
    return _STATUS_MAP.get(normalized, normalized)


def _flatten_search_attributes(
    attrs: dict[str, list[Any]] | None,
) -> dict[str, Any]:
    if not attrs:
        return {}
    flattened: dict[str, Any] = {}
    for key, values in attrs.items():
        if not values:
            continue
        flattened[key] = values[0] if len(values) == 1 else values
    return flattened


def _coerce_mapping(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _derive_phase(payload: dict[str, Any]) -> str | None:
    for key in (
        "phase",
        "state",
        "wallet_state",
        "rotation_state",
        "revocation_state",
        "delegation_state",
        "negotiation_state",
    ):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _derive_progress_percent(payload: dict[str, Any], status: str) -> int | None:
    value = payload.get("progress_percent")
    if isinstance(value, int):
        return max(0, min(100, value))

    score = payload.get("completeness_score")
    if isinstance(score, (float, int)):
        percent = int(round(score * 100)) if score <= 1 else int(round(score))
        return max(0, min(100, percent))

    if status == "completed":
        return 100
    return None


def _derive_links(payload: dict[str, Any]) -> dict[str, str]:
    links: dict[str, str] = {}
    external_refs = payload.get("external_refs")
    if isinstance(external_refs, dict):
        for key, value in external_refs.items():
            if isinstance(value, str) and value:
                links[key] = value
    for key, value in payload.items():
        if not isinstance(value, str) or not value:
            continue
        if key.endswith("_url"):
            links[key] = value
    return links


def _runtime_state_from_query(
    *,
    query_result: Any,
    status: str,
    updated_at: datetime | None,
    search_attributes: dict[str, Any],
) -> ProcedureRuntimeState:
    if isinstance(query_result, ProcedureRuntimeState):
        return query_result

    payload = _coerce_mapping(query_result)
    phase = _derive_phase(payload) or ""
    blocking_reason = payload.get("blocking_reason")
    failure_message = ""
    if isinstance(blocking_reason, str) and blocking_reason and status in _TERMINAL_STATUSES:
        failure_message = blocking_reason

    return ProcedureRuntimeState(
        status=status,
        phase=phase,
        updated_at=updated_at or utc_now(),
        failure_message=failure_message,
        progress_percent=_derive_progress_percent(payload, status) or 0,
        search_attributes=search_attributes,
        links=_derive_links(payload),
    )


def _dto_from_runtime(
    *,
    workflow_id: str,
    procedure_type: str,
    tenant_id: str,
    runtime_state: ProcedureRuntimeState,
    result: Any | None = None,
    started_at: datetime | None = None,
) -> ProcedureStatusDTO:
    raw_status = getattr(runtime_state.status, "value", runtime_state.status)
    return ProcedureStatusDTO(
        workflow_id=workflow_id,
        procedure_type=procedure_type,
        tenant_id=tenant_id,
        status=_normalize_status(str(raw_status)),
        phase=runtime_state.phase or None,
        progress_percent=runtime_state.progress_percent,
        result=result,
        failure_message=runtime_state.failure_message or None,
        search_attributes=runtime_state.search_attributes,
        links=runtime_state.links,
        started_at=started_at.isoformat() if started_at else None,
        updated_at=runtime_state.updated_at.isoformat(),
    )


def _dto_from_record(record: dict[str, Any]) -> ProcedureStatusDTO:
    return ProcedureStatusDTO(
        workflow_id=record["workflow_id"],
        procedure_type=record.get("procedure_type", ""),
        tenant_id=record.get("tenant_id", ""),
        status=_normalize_status(record.get("status")),
        phase=record.get("phase"),
        progress_percent=record.get("progress_percent"),
        result=record.get("result"),
        failure_message=record.get("failure_message"),
        search_attributes=record.get("search_attributes", {}) or {},
        links=record.get("links", {}) or {},
        started_at=record.get("started_at").isoformat() if record.get("started_at") else None,
        updated_at=record.get("updated_at").isoformat() if record.get("updated_at") else None,
    )


async def load_procedure_status(
    workflow_id: str,
    *,
    catalog: ProcedureCatalog | None = None,
    gateway: TemporalGateway | None = None,
    pool: Any | None = None,
) -> ProcedureStatusDTO | None:
    record: dict[str, Any] | None = None
    if pool is not None:
        record = await read_models.get_procedure(pool, workflow_id)

    if gateway is not None:
        try:
            description = await gateway.describe_workflow(workflow_id)
        except WorkflowNotFoundError:
            description = None
        except TemporalRpcError as exc:
            logger.warning(
                "procedure_status.describe_failed",
                workflow_id=workflow_id,
                error=str(exc),
                upstream_code=getattr(exc, "upstream_code", None),
            )
            description = None

        if description is not None:
            search_attributes = _flatten_search_attributes(description.search_attributes)
            procedure_type = str(
                search_attributes.get("procedure_type")
                or (record or {}).get("procedure_type", "")
                or description.workflow_type
            )
            tenant_id = str(
                search_attributes.get("tenant_id")
                or (record or {}).get("tenant_id", "")
            )
            status = _normalize_status(description.status.name if description.status else None)
            updated_at = (
                description.close_time
                or (record or {}).get("updated_at")
                or description.start_time
            )

            runtime_state = ProcedureRuntimeState(
                status=status,
                updated_at=updated_at or utc_now(),
                search_attributes=search_attributes,
            )
            if status == "running" and catalog is not None and procedure_type:
                try:
                    definition = catalog.resolve(procedure_type)
                    query_result = await gateway.query_workflow(workflow_id, definition.query_name)
                    runtime_state = _runtime_state_from_query(
                        query_result=query_result,
                        status=status,
                        updated_at=updated_at,
                        search_attributes=search_attributes,
                    )
                except ValueError:
                    logger.warning(
                        "procedure_status.unknown_definition",
                        workflow_id=workflow_id,
                        procedure_type=procedure_type,
                    )
                except WorkflowNotFoundError:
                    logger.warning(
                        "procedure_status.query_target_missing",
                        workflow_id=workflow_id,
                        procedure_type=procedure_type,
                    )
                except TemporalRpcError as exc:
                    logger.warning(
                        "procedure_status.query_failed",
                        workflow_id=workflow_id,
                        procedure_type=procedure_type,
                        error=str(exc),
                        upstream_code=getattr(exc, "upstream_code", None),
                    )

            result = (record or {}).get("result")
            if status == "completed" and result is None:
                try:
                    result = await gateway.get_result(workflow_id)
                except (TemporalRpcError, WorkflowNotFoundError) as exc:
                    logger.warning(
                        "procedure_status.result_failed",
                        workflow_id=workflow_id,
                        error=str(exc),
                        upstream_code=getattr(exc, "upstream_code", None),
                    )

            if record and record.get("failure_message") and not runtime_state.failure_message:
                runtime_state = ProcedureRuntimeState(
                    status=runtime_state.status,
                    phase=runtime_state.phase,
                    updated_at=runtime_state.updated_at,
                    failure_message=record["failure_message"],
                    progress_percent=runtime_state.progress_percent,
                    search_attributes=runtime_state.search_attributes,
                    links=runtime_state.links,
                )

            return _dto_from_runtime(
                workflow_id=workflow_id,
                procedure_type=procedure_type,
                tenant_id=tenant_id,
                runtime_state=runtime_state,
                result=result,
                started_at=description.start_time,
            )

    if record is None:
        return None

    return _dto_from_record(record)
