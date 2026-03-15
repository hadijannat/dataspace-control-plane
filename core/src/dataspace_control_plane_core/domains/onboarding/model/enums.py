from enum import Enum


class OnboardingPhase(str, Enum):
    IDENTITY_REGISTRATION = "identity_registration"
    DID_PROVISIONING = "did_provisioning"
    CREDENTIAL_ISSUANCE = "credential_issuance"
    CONNECTOR_BOOTSTRAP = "connector_bootstrap"
    TRUST_ANCHOR_REGISTRATION = "trust_anchor_registration"
    COMPLETED = "completed"
    FAILED = "failed"


class OnboardingStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
