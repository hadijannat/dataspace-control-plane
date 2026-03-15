from enum import Enum

class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    OFFBOARDED = "offboarded"

class EnvironmentTier(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class IdentifierScheme(str, Enum):
    BPNL = "BPNL"   # Catena-X legal entity
    BPNS = "BPNS"   # Catena-X site
    BPNA = "BPNA"   # Catena-X address
    LEI = "LEI"      # Legal Entity Identifier
    GLN = "GLN"      # GS1 Global Location Number
    DUNS = "DUNS"    # D&B DUNS
    CUSTOM = "CUSTOM"
