"""
Desired state model: declarative specification of all resources this agent manages.
Loaded from YAML manifests in desired_state_dir.
Secrets are reference paths, not raw values.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class KeycloakClientSpec:
    client_id: str
    name: str
    protocol: str = "openid-connect"
    public_client: bool = False
    redirect_uris: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    # Secret reference path (e.g. "vault:secret/keycloak/web-console-secret")
    secret_ref: str | None = None


@dataclass
class KeycloakRealmSpec:
    realm: str
    display_name: str
    enabled: bool = True
    clients: list[KeycloakClientSpec] = field(default_factory=list)


@dataclass
class DesiredState:
    keycloak_realms: list[KeycloakRealmSpec] = field(default_factory=list)
    edc_registrations: list[dict[str, Any]] = field(default_factory=list)
    worker_namespaces: list[str] = field(default_factory=list)
    tenant_bootstraps: list[dict[str, Any]] = field(default_factory=list)
