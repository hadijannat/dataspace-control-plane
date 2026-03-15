from enum import Enum

class RoleScope(str, Enum):
    PLATFORM = "platform"
    TENANT = "tenant"
    LEGAL_ENTITY = "legal_entity"
    SITE = "site"
    ENVIRONMENT = "environment"

class PermissionAction(str, Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    APPROVE = "approve"
    ADMIN = "admin"

class GrantStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
