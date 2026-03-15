"""
Generic repository and unit-of-work protocols used by all aggregate roots.
Adapters implement these; core only defines the interface.
"""
from __future__ import annotations
from typing import Generic, Protocol, TypeVar, runtime_checkable
from uuid import UUID

from .ids import AggregateId, TenantId
from .aggregate import AggregateRoot

AggT = TypeVar("AggT", bound=AggregateRoot)


@runtime_checkable
class Repository(Protocol[AggT]):
    """
    Generic repository protocol.
    - get: load by aggregate ID; raises NotFoundError if absent
    - save: persist with optimistic concurrency; raises StaleAggregateError on version mismatch
    - list: filtered listing; filters is a domain-specific dict, adapter translates to SQL/query
    """

    async def get(self, id: AggregateId, tenant_id: TenantId) -> AggT:
        ...

    async def save(self, aggregate: AggT, expected_version: int) -> None:
        ...

    async def list(self, tenant_id: TenantId, filters: dict | None = None, limit: int = 50, offset: int = 0) -> list[AggT]:
        ...


class UnitOfWork(Protocol):
    """
    Optional unit-of-work boundary for multi-aggregate operations.
    Adapters implement this; core defines the interface only.
    """

    async def __aenter__(self) -> "UnitOfWork":
        ...

    async def __aexit__(self, *args: object) -> None:
        ...

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...
