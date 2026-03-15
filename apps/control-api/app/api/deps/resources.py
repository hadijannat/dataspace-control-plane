from __future__ import annotations

from fastapi import HTTPException, Request, status

from app.services.procedure_catalog import ProcedureCatalog
from app.services.temporal_gateway import TemporalGateway


def _require_state_attr(request: Request, name: str, detail: str):
    value = getattr(request.app.state, name, None)
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
        )
    return value


def get_database_pool(request: Request):
    return _require_state_attr(
        request,
        "database_pool",
        "read model not available",
    )


def get_temporal_gateway(request: Request) -> TemporalGateway:
    client = _require_state_attr(
        request,
        "temporal_client",
        "workflow runtime not available",
    )
    return TemporalGateway(client)


def maybe_get_database_pool(request: Request):
    return getattr(request.app.state, "database_pool", None)


def maybe_get_temporal_gateway(request: Request) -> TemporalGateway | None:
    client = getattr(request.app.state, "temporal_client", None)
    return TemporalGateway(client) if client is not None else None

def get_procedure_catalog(request: Request) -> ProcedureCatalog:
    return _require_state_attr(
        request,
        "procedure_catalog",
        "procedure catalog not available",
    )


def get_idempotency_store(request: Request):
    return _require_state_attr(
        request,
        "idempotency_store",
        "idempotency store not available",
    )
