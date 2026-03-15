from __future__ import annotations
from dataclasses import dataclass
from datetime import date
from typing import Optional

from dataspace_control_plane_core.domains._shared.ids import TenantId, LegalEntityId, SiteId


@dataclass(frozen=True)
class Address:
    street: str
    city: str
    postal_code: str
    country_code: str  # ISO 3166-1 alpha-2
    region: str | None = None

    def formatted(self) -> str:
        region = f", {self.region}" if self.region else ""
        return f"{self.street}, {self.postal_code} {self.city}{region}, {self.country_code}"


@dataclass(frozen=True)
class ExternalIdentifier:
    """Generic external identifier — supports BPN, LEI, DUNS, GLN, and custom schemes."""
    scheme: str               # Use IdentifierScheme values or custom string
    value: str
    issuer: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None

    def is_expired(self, as_of: date) -> bool:
        return self.valid_to is not None and self.valid_to < as_of


@dataclass(frozen=True)
class TopologySnapshot:
    """Point-in-time snapshot of a legal entity's topology for cross-domain reads."""
    tenant_id: TenantId
    legal_entity_id: LegalEntityId
    display_name: str
    external_identifiers: tuple[ExternalIdentifier, ...]
    site_ids: tuple[SiteId, ...]
    environment_ids: tuple[str, ...] = ()
