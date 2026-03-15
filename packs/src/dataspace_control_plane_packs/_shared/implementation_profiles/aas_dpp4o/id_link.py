"""AAS asset identifier linking utilities for DPP4.0.

Links DPP-specific identifiers (e.g. battery identifier, ESPR product identifier)
to AAS asset administration shells using the AAS Part 2 API identifier encoding.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .aas_release_25_01 import AasId


@dataclass(frozen=True)
class IdLink:
    """A bidirectional link between a domain identifier and an AAS shell ID."""

    domain_id: str
    """The regulation or ecosystem-level identifier (e.g. battery_id, epc_id)."""

    aas_id: str
    """The AAS asset administration shell global asset ID (IRI)."""

    scheme: str
    """Identifier scheme name (e.g. ``battery_reg``, ``epc_gs1``, ``espr_dpp``)."""

    link_version: str = "1.0"

    def aas_id_base64url(self) -> str:
        """Return the base64url-encoded AAS ID for use in AAS Part 2 API paths."""
        return AasId(self.aas_id).base64url()

    def as_dict(self) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "aas_id": self.aas_id,
            "scheme": self.scheme,
            "link_version": self.link_version,
            "aas_id_base64url": self.aas_id_base64url(),
        }


def build_aas_id(namespace: str, domain_id: str) -> str:
    """Construct a canonical AAS IRI from a namespace and domain identifier.

    Convention: ``urn:<namespace>:<domain_id>``
    Callers should override this with organization-specific IRI patterns.
    """
    safe_id = domain_id.replace("/", "_").replace(":", "_")
    return f"urn:{namespace}:{safe_id}"


def build_id_link(
    domain_id: str,
    *,
    namespace: str,
    scheme: str,
    aas_id: str | None = None,
) -> IdLink:
    """Build an IdLink, generating the AAS IRI if not provided."""
    resolved_aas_id = aas_id or build_aas_id(namespace, domain_id)
    return IdLink(domain_id=domain_id, aas_id=resolved_aas_id, scheme=scheme)
