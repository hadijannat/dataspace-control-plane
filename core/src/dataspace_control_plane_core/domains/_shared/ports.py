"""Framework-neutral repository and unit-of-work protocols."""
from __future__ import annotations

from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

from .aggregate import AggregateRoot
from .ids import AggregateId, TenantId

AggT = TypeVar("AggT", bound=AggregateRoot)


@runtime_checkable
class Repository(Protocol[AggT]):
    """
    Generic optimistic-concurrency repository contract.

    Domain-specific repositories may extend this protocol with richer read
    queries, but aggregate persistence stays consistent across the kernel.
    """

    async def get(self, id: AggregateId, tenant_id: TenantId) -> AggT:
        ...

    async def save(self, aggregate: AggT, expected_version: int) -> None:
        ...

    async def list(
        self,
        tenant_id: TenantId,
        filters: dict[str, Any] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AggT]:
        ...


class UnitOfWork(Protocol):
    """Optional transaction boundary for multi-aggregate use cases."""

    async def __aenter__(self) -> "UnitOfWork":
        ...

    async def __aexit__(self, *args: object) -> None:
        ...

    async def commit(self) -> None:
        ...

    async def rollback(self) -> None:
        ...
