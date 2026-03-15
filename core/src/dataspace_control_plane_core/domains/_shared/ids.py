"""
Typed value objects and factories for aggregate and cross-cutting identifiers.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterator, Protocol
from uuid import UUID, uuid4


class UuidFactory(Protocol):
    """Low-level UUID generator abstraction."""

    def new_uuid(self) -> UUID:
        ...


class IdFactory(Protocol):
    """High-level ID factory abstraction used by the semantic kernel."""

    def new_aggregate_id(self) -> "AggregateId":
        ...

    def new_workflow_id(self) -> "WorkflowId":
        ...

    def new_event_id(self) -> UUID:
        ...

    def new_request_id(self) -> str:
        ...


class SystemUuidFactory:
    """Production UUID factory."""

    def new_uuid(self) -> UUID:
        return uuid4()


class SystemIdFactory:
    """Production ID factory backed by UUID4 values."""

    def __init__(self, uuid_factory: UuidFactory | None = None) -> None:
        self._uuid_factory = uuid_factory or SystemUuidFactory()

    def new_aggregate_id(self) -> "AggregateId":
        return AggregateId(self._uuid_factory.new_uuid())

    def new_workflow_id(self) -> "WorkflowId":
        return WorkflowId(str(self._uuid_factory.new_uuid()))

    def new_event_id(self) -> UUID:
        return self._uuid_factory.new_uuid()

    def new_request_id(self) -> str:
        return str(self._uuid_factory.new_uuid())


_DEFAULT_ID_FACTORY: ContextVar[IdFactory] = ContextVar(
    "dataspace_control_plane_core_default_id_factory",
    default=SystemIdFactory(),
)


def default_id_factory() -> IdFactory:
    """Return the active shared ID factory."""
    return _DEFAULT_ID_FACTORY.get()


@contextmanager
def use_id_factory(factory: IdFactory) -> Iterator[IdFactory]:
    """Temporarily override the shared ID factory."""
    token = _DEFAULT_ID_FACTORY.set(factory)
    try:
        yield factory
    finally:
        _DEFAULT_ID_FACTORY.reset(token)


@dataclass(frozen=True)
class AggregateId:
    """Generic aggregate root identifier backed by a UUID."""

    value: UUID

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def generate(cls, factory: IdFactory | None = None) -> "AggregateId":
        return (factory or default_id_factory()).new_aggregate_id()

    @classmethod
    def from_str(cls, raw: str) -> "AggregateId":
        return cls(UUID(str(raw).strip()))


@dataclass(frozen=True)
class StringIdentifier:
    """Base type for opaque string identifiers."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise ValueError(f"{type(self).__name__} must not be blank")
        object.__setattr__(self, "value", normalized)

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class TenantId(StringIdentifier):
    """Opaque identifier for a platform tenant."""


@dataclass(frozen=True)
class LegalEntityId(StringIdentifier):
    """Identifier for a legal entity within a tenant."""


@dataclass(frozen=True)
class SiteId(StringIdentifier):
    """Identifier for a physical or logical site."""


@dataclass(frozen=True)
class EnvironmentId(StringIdentifier):
    """Identifier for a deployment environment."""


@dataclass(frozen=True)
class WorkflowId(StringIdentifier):
    """Durable workflow execution identifier."""

    @classmethod
    def generate(cls, factory: IdFactory | None = None) -> "WorkflowId":
        return (factory or default_id_factory()).new_workflow_id()
