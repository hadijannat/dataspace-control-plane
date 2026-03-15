"""
Actual state model: discovered current state of all managed resources.
Populated by drivers querying real systems.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class KeycloakRealmActual:
    realm: str
    enabled: bool
    client_ids: list[str] = field(default_factory=list)


@dataclass
class ActualState:
    keycloak_realms: list[KeycloakRealmActual] = field(default_factory=list)
    edc_registrations: list[dict[str, Any]] = field(default_factory=list)
    worker_namespaces: list[str] = field(default_factory=list)
    tenant_bootstraps: list[dict[str, Any]] = field(default_factory=list)
