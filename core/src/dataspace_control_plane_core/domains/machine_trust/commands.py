from __future__ import annotations
from dataclasses import dataclass
from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId
from dataspace_control_plane_core.domains._shared.actor import ActorRef
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from dataspace_control_plane_core.canonical_models.identity import DidUri, CredentialEnvelope


@dataclass(frozen=True)
class RegisterDidCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    did: DidUri
    actor: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class AddCredentialCommand:
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    credential: CredentialEnvelope
    actor: ActorRef
    correlation: CorrelationContext


@dataclass(frozen=True)
class RevokeCredentialCommand:
    tenant_id: TenantId
    credential_id: str
    reason: str
    actor: ActorRef
    correlation: CorrelationContext
