from __future__ import annotations

from dataclasses import dataclass, field

from dataspace_control_plane_procedures._shared.compensation import CompensationMarker
from dataspace_control_plane_procedures._shared.manual_review import ManualReviewState


@dataclass(frozen=True)
class ConnectorStartInput:
    tenant_id: str
    legal_entity_id: str
    environment: str
    binding_name: str
    connector_url: str
    wallet_ref: str = ""
    pack_id: str = "catena-x"
    idempotency_key: str = ""


@dataclass(frozen=True)
class ConnectorResult:
    workflow_id: str
    status: str
    connector_binding_id: str
    dataspace_connector_id: str = ""
    discovery_endpoint: str = ""


@dataclass(frozen=True)
class ConnectorStatusQuery:
    state: str
    blocking_reason: str
    connector_url: str
    dataspace_registered: bool
    wallet_linked: bool
    is_healthy: bool


@dataclass
class ConnectorCarryState:
    """Carry-over state for Continue-As-New boundaries."""
    connector_state: str
    connector_binding_id: str
    dataspace_connector_id: str
    discovery_endpoint: str
    plan_ref: str
    infra_apply_ref: str
    wallet_ref: str
    wallet_linked: bool
    dataspace_registered: bool
    last_health_check: str
    dedupe_ids: set[str] = field(default_factory=set)
    manual_review: ManualReviewState = field(default_factory=ManualReviewState)
    compensation_markers: list[CompensationMarker] = field(default_factory=list)
    iteration: int = 0
