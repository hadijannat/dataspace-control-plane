"""Enumerations for the metering_finops domain."""
from enum import Enum


class MeteringDimension(str, Enum):
    DATA_BYTES = "data_bytes"
    API_CALLS = "api_calls"
    ACTIVE_AGREEMENTS = "active_agreements"
    CONNECTOR_HOURS = "connector_hours"
    ASSET_PUBLICATIONS = "asset_publications"


class ChargeStatementStatus(str, Enum):
    DRAFT = "draft"
    FINALIZED = "finalized"
    EXPORTED = "exported"


class QuotaStatus(str, Enum):
    WITHIN_QUOTA = "within_quota"
    APPROACHING_LIMIT = "approaching_limit"
    QUOTA_EXCEEDED = "quota_exceeded"
