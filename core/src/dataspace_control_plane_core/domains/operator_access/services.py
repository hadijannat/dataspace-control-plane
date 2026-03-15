from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4

from dataspace_control_plane_core.domains._shared.time import Clock, UtcClock
from .model.aggregates import Grant, AuthorizationDecision, OperatorPrincipal
from .model.value_objects import Scope, PermissionAction
from .model.enums import GrantStatus
from .commands import GrantRoleCommand, RevokeGrantCommand, CheckAuthorizationCommand
from .events import RoleGranted, GrantRevoked
from .ports import GrantRepository


class AuthorizationService:
    """Pure authorization logic. No HTTP, no Keycloak calls."""

    def __init__(self, repo: GrantRepository, clock: Clock = UtcClock()) -> None:
        self._repo = repo
        self._clock = clock

    async def grant_role(self, cmd: GrantRoleCommand) -> Grant:
        grant = Grant(
            grant_id=str(uuid4()),
            subject=cmd.subject,
            role_name=cmd.role_name,
            scope=cmd.scope,
            granted_by=cmd.granted_by.subject,
            granted_at=self._clock.now(),
            expires_at=cmd.expires_at,
            status=GrantStatus.ACTIVE,
        )
        await self._repo.save(grant)
        return grant

    async def revoke_grant(self, cmd: RevokeGrantCommand) -> Grant:
        grant = await self._repo.get(cmd.grant_id)
        grant = Grant(**{**grant.__dict__, "status": GrantStatus.REVOKED})
        await self._repo.save(grant)
        return grant

    def decide(self, principal: OperatorPrincipal, action: str, resource_type: str, resource_id: str | None = None) -> AuthorizationDecision:
        scope = Scope(resource_type=resource_type, resource_id=resource_id)
        # Platform admins always allowed
        if principal.has_realm_role("platform_admin"):
            return AuthorizationDecision(allowed=True, reason="platform_admin role")
        # Tenant access check
        if resource_id and not principal.can_access_tenant(resource_id):
            return AuthorizationDecision(allowed=False, reason="principal lacks tenant access")
        return AuthorizationDecision(allowed=True, reason="tenant access granted")
