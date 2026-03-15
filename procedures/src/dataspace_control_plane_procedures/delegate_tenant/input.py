from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DelegationStartInput:
    tenant_id: str
    parent_legal_entity_id: str
    legal_entity_id: str                  # child
    child_legal_entity_name: str
    child_bpnl: str = ""
    connector_mode: str = "auto"          # "shared" | "dedicated" | "auto"
    parent_connector_ref: str = ""
    pack_id: str = "default"


@dataclass(frozen=True)
class DelegationResult:
    workflow_id: str
    status: str
    child_topology_ref: str = ""
    delegation_ref: str = ""
    connector_mode: str = ""
    connector_ref: str = ""


@dataclass(frozen=True)
class DelegationStatusQuery:
    delegation_state: str
    connector_mode: str
    is_verified: bool
    blocking_reason: str


@dataclass
class DelegationCarryState:
    """Carry-over state for Continue-As-New boundaries (reserved for future use)."""
    delegation_state: str
    child_topology_ref: str
    delegation_ref: str
    connector_mode: str
    connector_ref: str
    dedupe_ids: set[str] = field(default_factory=set)
