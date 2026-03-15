from __future__ import annotations
from dataclasses import dataclass
from .enums import RoleScope, PermissionAction


@dataclass(frozen=True)
class Scope:
    """An authorization scope: resource_type + optional resource_id."""
    resource_type: str   # e.g. "tenant", "legal_entity", "site", "environment", "*"
    resource_id: str | None = None  # None = all resources of that type


@dataclass(frozen=True)
class Permission:
    action: PermissionAction
    scope: Scope


@dataclass(frozen=True)
class Role:
    name: str
    role_scope: RoleScope
    permissions: frozenset[Permission]

    def can(self, action: PermissionAction, scope: Scope) -> bool:
        return any(
            p.action == action and (
                p.scope.resource_type == "*" or
                p.scope.resource_type == scope.resource_type
            )
            for p in self.permissions
        )
