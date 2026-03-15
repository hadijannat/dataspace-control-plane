from enum import Enum

class NegotiationStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CONCLUDED = "concluded"
    TERMINATED = "terminated"

class EntitlementStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"
