"""
ActorRef: typed reference to any actor that can initiate a command or receive an event.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class ActorType(str, Enum):
    HUMAN = "human"
    SERVICE = "service"
    WORKFLOW = "workflow"
    EXTERNAL_PARTICIPANT = "external_participant"
    SYSTEM = "system"


@dataclass(frozen=True)
class ActorRef:
    """
    Immutable reference to an actor.
    subject: the unique identifier (user sub, service account name, workflow ID, participant BPN)
    actor_type: category for policy evaluation and audit
    tenant_id: optional — system actors may not be tenant-scoped
    display_name: human-readable label for audit display
    """
    subject: str
    actor_type: ActorType
    tenant_id: str | None = None
    display_name: str | None = None

    def is_human(self) -> bool:
        return self.actor_type == ActorType.HUMAN

    def is_service(self) -> bool:
        return self.actor_type == ActorType.SERVICE

    def __str__(self) -> str:
        return f"{self.actor_type.value}:{self.subject}"
