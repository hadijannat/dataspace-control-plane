"""
Operator tenant endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps.auth import get_current_principal
from app.api.deps.resources import get_database_pool
from app.api.schemas.common import PaginatedResponse
from app.auth.principals import Principal
from app.services import read_models

router = APIRouter()


class TenantSummary(BaseModel):
    """Compact tenant record returned by list and get endpoints."""

    tenant_id: str
    display_name: str
    status: str
    legal_entity_id: str | None = None


@router.get(
    "/",
    operation_id="operator_list_tenants",
    response_model=PaginatedResponse[TenantSummary],
)
async def list_tenants(
    limit: int = 50,
    offset: int = 0,
    principal: Principal = Depends(get_current_principal),
    pool = Depends(get_database_pool),
) -> PaginatedResponse[TenantSummary]:
    """
    Return a paginated list of tenants visible to the authenticated principal.

    Admin principals (``dataspace-admin`` realm role) see all tenants.
    Non-admin principals see only the tenants in their ``tenant_ids`` claim,
    which is enforced by the read-model query once full RBAC is wired.

    Returns a consistent paginated response body for the SPA and generated SDK.
    """
    tenant_filter = None if principal.has_role("dataspace-admin") else sorted(principal.tenant_ids)
    if tenant_filter == []:
        return PaginatedResponse[TenantSummary](
            items=[],
            total=0,
            limit=limit,
            offset=offset,
        )
    rows = await read_models.list_tenants(
        pool,
        limit=limit,
        offset=offset,
        tenant_ids=tenant_filter,
    )
    total = await read_models.count_tenants(pool, tenant_filter)
    return PaginatedResponse[TenantSummary](
        items=[
            TenantSummary(
                tenant_id=row["tenant_id"],
                display_name=row.get("display_name", row["tenant_id"]),
                status=row.get("status", "UNKNOWN"),
                legal_entity_id=row.get("legal_entity_id"),
            )
            for row in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{tenant_id}",
    operation_id="operator_get_tenant",
    response_model=TenantSummary,
)
async def get_tenant(
    tenant_id: str,
    principal: Principal = Depends(get_current_principal),
    pool = Depends(get_database_pool),
) -> TenantSummary:
    """
    Return a single tenant record by its ``tenant_id``.

    Returns HTTP 403 if the principal does not have access to the requested
    tenant, HTTP 404 if the tenant does not exist, and HTTP 503 if the
    read-model pool is not yet available.
    """
    # Authorisation — principal must have access to this tenant.
    if not principal.can_access_tenant(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access to tenant '{tenant_id}' is not permitted",
        )

    row = await read_models.get_tenant(pool, tenant_id=tenant_id)

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found",
        )

    return TenantSummary(
        tenant_id=row["tenant_id"],
        display_name=row.get("display_name", row["tenant_id"]),
        status=row.get("status", "UNKNOWN"),
        legal_entity_id=row.get("legal_entity_id"),
    )
