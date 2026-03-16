"""
Query objects for procedure read operations (read side of CQRS-lite).

Queries are immutable value objects that describe what data is requested.
They carry no side effects and are constructed by route handlers and passed
to read-model facades.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class ListProceduresQuery:
    """
    Query to retrieve a paginated list of procedures for a tenant.

    Attributes
    ----------
    tenant_id:
        Tenant scope — all returned procedures belong to this tenant.
    status_filter:
        Optional status to filter on (e.g. ``"running"``, ``"completed"``).
        When ``None``, procedures of all statuses are returned.
    limit:
        Maximum number of results to return (default 50).
    offset:
        Number of results to skip for cursor-based pagination (default 0).
    """

    tenant_id: str
    status_filter: str | None = None
    limit: int = 50
    offset: int = 0


@dataclass(frozen=True)
class GetProcedureQuery:
    """
    Query to retrieve a single procedure by its workflow_id.

    Attributes
    ----------
    workflow_id:
        Temporal workflow identifier — unique across all tenants.
    tenant_id:
        Tenant scope — used to enforce tenancy boundaries on the result.
    """

    workflow_id: str
    tenant_id: str
