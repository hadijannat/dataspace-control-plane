"""Shared semantic-kernel primitives used across all domain packages."""

from .actor import ActorRef, ActorType
from .aggregate import AggregateRoot
from .correlation import CorrelationContext
from .errors import (
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionError,
    PreconditionError,
    StaleAggregateError,
    ValidationError,
)
from .events import DomainEvent
from .ids import (
    AggregateId,
    EnvironmentId,
    IdFactory,
    LegalEntityId,
    SiteId,
    TenantId,
    UuidFactory,
    WorkflowId,
    default_id_factory,
)
from .ports import Repository, UnitOfWork
from .time import Clock, FrozenClock, UtcClock, default_clock, utc_now
from .versioning import CURRENT_KERNEL_VERSION, VersionTag

__all__ = [
    "ActorRef",
    "ActorType",
    "AggregateId",
    "AggregateRoot",
    "Clock",
    "ConflictError",
    "CorrelationContext",
    "CURRENT_KERNEL_VERSION",
    "default_clock",
    "default_id_factory",
    "DomainError",
    "DomainEvent",
    "EnvironmentId",
    "FrozenClock",
    "IdFactory",
    "LegalEntityId",
    "NotFoundError",
    "PermissionError",
    "PreconditionError",
    "Repository",
    "SiteId",
    "StaleAggregateError",
    "TenantId",
    "UnitOfWork",
    "UtcClock",
    "UuidFactory",
    "utc_now",
    "ValidationError",
    "VersionTag",
    "WorkflowId",
]
