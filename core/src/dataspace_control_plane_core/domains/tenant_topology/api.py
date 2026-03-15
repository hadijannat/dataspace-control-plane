"""Public API surface for tenant_topology domain. Only import from here."""
from .services import TenantTopologyService
from .ports import LegalEntityRepository, TopologyLookupPort
from .commands import (
    RegisterLegalEntityCommand, AddExternalIdentifierCommand,
    ActivateLegalEntityCommand, RegisterEnvironmentCommand,
)
from .events import (
    LegalEntityRegistered, LegalEntityActivated,
    ExternalIdentifierAdded, EnvironmentRegistered,
)
from .model.aggregates import (
    EnterpriseGroup,
    Environment,
    LegalEntity,
    LegalEntityTopology,
    Site,
    Tenant,
    TenantTopology,
)
from .model.value_objects import ExternalIdentifier, TopologySnapshot, Address
from .model.enums import TenantStatus, EnvironmentTier, IdentifierScheme
from .errors import LegalEntityNotFoundError, DuplicateLegalEntityError

__all__ = [
    "TenantTopologyService",
    "LegalEntityRepository", "TopologyLookupPort",
    "RegisterLegalEntityCommand", "AddExternalIdentifierCommand",
    "ActivateLegalEntityCommand", "RegisterEnvironmentCommand",
    "LegalEntityRegistered", "LegalEntityActivated",
    "ExternalIdentifierAdded", "EnvironmentRegistered",
    "EnterpriseGroup", "Tenant", "LegalEntity",
    "TenantTopology", "LegalEntityTopology", "Site", "Environment",
    "ExternalIdentifier", "TopologySnapshot", "Address",
    "TenantStatus", "EnvironmentTier", "IdentifierScheme",
    "LegalEntityNotFoundError", "DuplicateLegalEntityError",
]
