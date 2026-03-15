from __future__ import annotations
from typing import Protocol
from dataspace_control_plane_core.domains._shared.ids import TenantId
from .model.aggregates import AuthorizationDecision, Grant, GrantAggregate, OperatorPrincipal
from .model.value_objects import Scope


class GrantRepository(Protocol):
    async def get(self, grant_id: str, tenant_id: TenantId | None = None) -> Grant | GrantAggregate: ...
    async def save(self, grant: Grant | GrantAggregate, tenant_id: TenantId | None = None) -> None: ...
    async def list_for_subject(self, subject: str, tenant_id: TenantId | None = None) -> list[Grant | GrantAggregate]: ...


class AuthorizationPort(Protocol):
    """Evaluate authorization decisions — pure function, no side effects."""
    def decide(self, principal: OperatorPrincipal, action: str, scope: Scope) -> AuthorizationDecision: ...
