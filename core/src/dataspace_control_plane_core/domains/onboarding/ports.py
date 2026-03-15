from typing import Protocol, runtime_checkable
from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId
from .model.aggregates import OnboardingCase


@runtime_checkable
class OnboardingCaseRepository(Protocol):
    """Persistence port for OnboardingCase aggregate."""

    async def get(self, tenant_id: TenantId, legal_entity_id: LegalEntityId) -> OnboardingCase: ...

    async def save(self, case: OnboardingCase, expected_version: int) -> None: ...

    async def find_by_legal_entity(
        self, tenant_id: TenantId, legal_entity_id: LegalEntityId
    ) -> OnboardingCase | None: ...


@runtime_checkable
class IdentityProvisioningPort(Protocol):
    """Adapter port for DID-based identity provisioning."""

    async def provision_did(
        self,
        tenant_id: TenantId,
        legal_entity_id: LegalEntityId,
        bpnl: str,
    ) -> str:
        """Provisions a DID for the given legal entity. Returns the DID string."""
        ...


@runtime_checkable
class ConnectorProvisioningPort(Protocol):
    """Adapter port for EDC connector bootstrap."""

    async def bootstrap_connector(
        self,
        tenant_id: TenantId,
        legal_entity_id: LegalEntityId,
        connector_url: str,
    ) -> None:
        """Bootstraps the connector at the given URL for the legal entity."""
        ...


TopologyLookupPort = IdentityProvisioningPort
TrustReadinessPort = IdentityProvisioningPort
ConnectorReadinessPort = ConnectorProvisioningPort
PolicyCatalogReadinessPort = ConnectorProvisioningPort
ComplianceBaselinePort = ConnectorProvisioningPort
