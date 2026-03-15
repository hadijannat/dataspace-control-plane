"""
Typed value objects for all aggregate and cross-cutting identifiers.
Use these instead of bare str/UUID to prevent primitive obsession.
"""
from __future__ import annotations
from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class AggregateId:
    """Generic aggregate root identifier backed by a UUID."""
    value: UUID

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def generate(cls) -> "AggregateId":
        return cls(uuid4())

    @classmethod
    def from_str(cls, s: str) -> "AggregateId":
        return cls(UUID(s))


@dataclass(frozen=True)
class TenantId:
    """Opaque identifier for a platform tenant."""
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("TenantId must not be blank")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class LegalEntityId:
    """Identifier for a legal entity within a tenant."""
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("LegalEntityId must not be blank")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class SiteId:
    """Identifier for a physical or logical site."""
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class EnvironmentId:
    """Identifier for a deployment environment (dev/staging/prod)."""
    value: str

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class WorkflowId:
    """Temporal workflow execution identifier. Matches Temporal's workflow_id field."""
    value: str

    def __str__(self) -> str:
        return self.value
