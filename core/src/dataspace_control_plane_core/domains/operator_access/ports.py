from __future__ import annotations
from typing import Protocol
from .model.aggregates import Grant, AuthorizationDecision, OperatorPrincipal
from .model.value_objects import Scope


class GrantRepository(Protocol):
    async def get(self, grant_id: str) -> Grant: ...
    async def save(self, grant: Grant) -> None: ...
    async def list_for_subject(self, subject: str) -> list[Grant]: ...


class AuthorizationPort(Protocol):
    """Evaluate authorization decisions — pure function, no side effects."""
    def decide(self, principal: OperatorPrincipal, action: str, scope: Scope) -> AuthorizationDecision: ...
