from __future__ import annotations
from typing import Protocol, runtime_checkable
from dataspace_control_plane_core.domains._shared.ids import AggregateId, TenantId, LegalEntityId
from .model.aggregates import NegotiationCase, Entitlement


@runtime_checkable
class NegotiationRepository(Protocol):
    async def get(self, tenant_id: TenantId, negotiation_id: AggregateId) -> NegotiationCase: ...
    async def save(self, tenant_id: TenantId, negotiation: NegotiationCase) -> None: ...
    async def list_for_legal_entity(
        self, tenant_id: TenantId, legal_entity_id: LegalEntityId
    ) -> list[NegotiationCase]: ...


@runtime_checkable
class EntitlementRepository(Protocol):
    async def get(self, tenant_id: TenantId, entitlement_id: AggregateId) -> Entitlement: ...
    async def save(self, tenant_id: TenantId, entitlement: Entitlement) -> None: ...
    async def list_for_agreement(
        self, tenant_id: TenantId, agreement_id: str
    ) -> list[Entitlement]: ...
    async def list_active_for_legal_entity(
        self, tenant_id: TenantId, legal_entity_id: LegalEntityId
    ) -> list[Entitlement]: ...


@runtime_checkable
class AgreementRegistryPort(Protocol):
    """Cross-boundary port: register concluded agreements with the external DSP catalog."""
    async def register_agreement(
        self, tenant_id: TenantId, agreement_id: str, policy_snapshot_id: str
    ) -> None: ...


@runtime_checkable
class CatalogLookupPort(Protocol):
    """Cross-boundary port: look up offer and asset metadata from the adapter layer."""
    async def get_asset_ref(self, tenant_id: TenantId, asset_id: str) -> dict: ...
    async def get_offer_policy_id(self, tenant_id: TenantId, offer_id: str) -> str: ...
