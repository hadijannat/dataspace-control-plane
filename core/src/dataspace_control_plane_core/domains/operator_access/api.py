"""Public API surface for operator_access domain."""
from .services import AuthorizationService
from .ports import GrantRepository, AuthorizationPort
from .commands import GrantRoleCommand, RevokeGrantCommand, CheckAuthorizationCommand
from .events import RoleGranted, GrantRevoked
from .model.aggregates import Grant, AuthorizationDecision, OperatorPrincipal, EmergencyAccessGrant
from .model.value_objects import Scope, Permission, Role
from .model.enums import RoleScope, PermissionAction, GrantStatus
from .errors import GrantNotFoundError, UnauthorizedError

__all__ = [
    "AuthorizationService",
    "GrantRepository", "AuthorizationPort",
    "GrantRoleCommand", "RevokeGrantCommand", "CheckAuthorizationCommand",
    "RoleGranted", "GrantRevoked",
    "Grant", "AuthorizationDecision", "OperatorPrincipal", "EmergencyAccessGrant",
    "Scope", "Permission", "Role",
    "RoleScope", "PermissionAction", "GrantStatus",
    "GrantNotFoundError", "UnauthorizedError",
]
