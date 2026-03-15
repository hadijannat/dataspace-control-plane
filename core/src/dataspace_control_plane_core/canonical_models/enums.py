"""Shared enumerations referenced across canonical models."""
from enum import Enum


class CredentialFormat(str, Enum):
    JWT_VC = "jwt_vc"
    JWT_VC_JSON = "jwt_vc_json"
    LD_PROOF = "ld_proof"
    SD_JWT = "sd_jwt"


class PolicyEffect(str, Enum):
    PERMIT = "permit"
    PROHIBIT = "prohibit"
    OBLIGATE = "obligate"


class TwinPublicationStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    RETRACTED = "retracted"
    ARCHIVED = "archived"


class NegotiationState(str, Enum):
    REQUESTED = "REQUESTED"
    OFFERED = "OFFERED"
    ACCEPTED = "ACCEPTED"
    AGREED = "AGREED"
    VERIFIED = "VERIFIED"
    FINALIZED = "FINALIZED"
    TERMINATED = "TERMINATED"


class RetentionClass(str, Enum):
    INDEFINITE = "indefinite"
    SEVEN_YEARS = "seven_years"
    TEN_YEARS = "ten_years"
    CUSTOM = "custom"


class RedactionClass(str, Enum):
    NONE = "none"
    PARTIAL = "partial"
    FULL = "full"
