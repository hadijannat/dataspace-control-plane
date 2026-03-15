"""Typed references to humans, services, workflows, and external participants."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .ids import TenantId


class ActorType(str, Enum):
    HUMAN = "human"
    SERVICE = "service"
    WORKFLOW = "workflow"
    EXTERNAL_PARTICIPANT = "external_participant"
    SYSTEM = "system"


@dataclass(frozen=True)
class ActorRef:
    """
    Immutable reference to an actor that initiated or approved an action.

    ``subject`` remains a transport-neutral opaque identifier. Runtime-specific
    token parsing stays outside ``core``.
    """

    subject: str
    actor_type: ActorType
    tenant_id: TenantId | None = None
    display_name: str | None = None

    def __post_init__(self) -> None:
        if not self.subject.strip():
            raise ValueError("ActorRef.subject must not be blank")

    def is_human(self) -> bool:
        return self.actor_type == ActorType.HUMAN

    def is_service(self) -> bool:
        return self.actor_type == ActorType.SERVICE

    def __str__(self) -> str:
        return f"{self.actor_type.value}:{self.subject}"
