from __future__ import annotations
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId
from dataspace_control_plane_core.domains._shared.time import Clock, UtcClock
from .model.aggregates import AuthorizationDecision, Grant, GrantAggregate, OperatorPrincipal
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
        tenant_id = TenantId(cmd.scope.tenant_hint() or "platform")
        aggregate = GrantAggregate(
            id=AggregateId.generate(),
            tenant_id=tenant_id,
            principal_subject=cmd.subject,
            scope=cmd.scope,
            granted_by=cmd.granted_by.subject,
            granted_at=self._clock.now(),
            expires_at=cmd.expires_at,
            status=GrantStatus.ACTIVE,
        )
        aggregate._raise_event(RoleGranted(
            tenant_id=tenant_id,
            subject=cmd.subject,
            role_name=cmd.role_name,
            scope_resource=cmd.scope.resource_type,
            correlation=cmd.correlation,
        ))
        await self._repo.save(aggregate, tenant_id=tenant_id)
        return Grant(
            grant_id=aggregate.grant_id,
            subject=aggregate.principal_subject,
            role_name=cmd.role_name,
            scope=aggregate.scope,
            granted_by=aggregate.granted_by,
            granted_at=aggregate.granted_at,
            expires_at=aggregate.expires_at,
            status=aggregate.status,
        )

    async def revoke_grant(self, cmd: RevokeGrantCommand) -> Grant:
        loaded = await self._repo.get(cmd.grant_id)
        if isinstance(loaded, GrantAggregate):
            loaded.revoke()
            loaded._raise_event(GrantRevoked(
                tenant_id=loaded.tenant_id,
                grant_id=loaded.grant_id,
                subject=loaded.principal_subject,
                correlation=cmd.correlation,
            ))
            await self._repo.save(loaded, tenant_id=loaded.tenant_id)
            return Grant(
                grant_id=loaded.grant_id,
                subject=loaded.principal_subject,
                role_name=loaded.role.name if loaded.role else "",
                scope=loaded.scope,
                granted_by=loaded.granted_by,
                granted_at=loaded.granted_at,
                expires_at=loaded.expires_at,
                status=loaded.status,
            )
        grant = Grant(**{**loaded.__dict__, "status": GrantStatus.REVOKED})
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
