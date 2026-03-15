from __future__ import annotations

from typing import Any

from app.application.dto.procedures import ProcedureStatusDTO
from app.services import read_models
from app.services.temporal_gateway import TemporalGateway


_STATUS_MAP = {
    "CANCELED": "CANCELLED",
    "TERMINATED": "TERMINATED",
}


def _normalize_status(raw_status: str | None) -> str:
    if raw_status is None:
        return "RUNNING"
    return _STATUS_MAP.get(raw_status, raw_status)


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


async def load_procedure_status(
    workflow_id: str,
    *,
    gateway: TemporalGateway | None = None,
    pool: Any | None = None,
) -> ProcedureStatusDTO | None:
    if gateway is not None:
        try:
            description = await gateway.describe_workflow(workflow_id)
            search_attributes = _flatten_search_attributes(description.search_attributes)
            return ProcedureStatusDTO(
                workflow_id=description.id,
                procedure_type=str(search_attributes.get("procedure_type", description.workflow_type)),
                tenant_id=str(search_attributes.get("tenant_id", "")),
                status=_normalize_status(description.status.name if description.status else None),
                search_attributes=search_attributes,
                started_at=description.start_time.isoformat(),
            )
        except Exception:
            pass

    if pool is None:
        return None

    record = await read_models.get_procedure(pool, workflow_id)
    if record is None:
        return None

    return ProcedureStatusDTO(
        workflow_id=record["workflow_id"],
        procedure_type=record.get("procedure_type", ""),
        tenant_id=record.get("tenant_id", ""),
        status=_normalize_status(record.get("status")),
        result=record.get("result"),
        failure_message=record.get("failure_message"),
        search_attributes=record.get("search_attributes", {}) or {},
        started_at=record.get("started_at").isoformat() if record.get("started_at") else None,
        updated_at=record.get("updated_at").isoformat() if record.get("updated_at") else None,
    )
