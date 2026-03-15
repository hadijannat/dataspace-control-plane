from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Any

from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId, SiteId, EnvironmentId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from .model.enums import EnvironmentTier


@dataclass(frozen=True)
class RegisterLegalEntityCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    display_name: str
    registered_name: str
    actor: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class AddExternalIdentifierCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    scheme: str
    value: str
    issuer: str | None
    valid_from: date | None
    valid_to: date | None
    actor: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class ActivateLegalEntityCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    actor: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class RegisterEnvironmentCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    environment_id: EnvironmentId
    tier: EnvironmentTier
    display_name: str
    connector_url: str | None
    actor: ActorRef
    correlation: CorrelationContext
