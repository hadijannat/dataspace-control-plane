"""Gaia-X Trust Framework version constants and version model.

Normative reference: Gaia-X Trust Framework 22.10
https://docs.gaia-x.eu/policy-rules-committee/trust-framework/22.10/

This module is data-only.  No HTTP, no persistence.
"""
from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Version constants
# ---------------------------------------------------------------------------

GX_TRUST_FRAMEWORK_VERSION = "22.10"
GX_TRUST_FRAMEWORK_URI = (
    "https://docs.gaia-x.eu/policy-rules-committee/trust-framework/22.10/"
)

# GX-23 VC/SD vocabulary namespace
GX_VOCABULARY_URI = "https://w3id.org/gaia-x/deployment#"
GX_W3C_VC_CONTEXT = "https://www.w3.org/2018/credentials/v1"
GX_ODRL_CONTEXT = "https://www.w3.org/ns/odrl.jsonld"


@dataclass(frozen=True)
class GaiaXTrustFrameworkVersion:
    """A specific release of the Gaia-X Trust Framework.

    Attributes:
        version:        Release label (e.g. ``"22.10"``).
        uri:            Canonical URI for this release.
        effective_from: ISO 8601 date string on which this version became effective.
        effective_to:   ISO 8601 date string on which this version was superseded,
                        or None if still in force.
    """

    version: str
    uri: str
    effective_from: str
    effective_to: str | None = None


# ---------------------------------------------------------------------------
# Known framework releases (add new entries as they are published)
# ---------------------------------------------------------------------------

GX_FRAMEWORK_22_10 = GaiaXTrustFrameworkVersion(
    version="22.10",
    uri="https://docs.gaia-x.eu/policy-rules-committee/trust-framework/22.10/",
    effective_from="2022-10-01",
    effective_to=None,
)
"""Gaia-X Trust Framework 22.10 (currently in force as of 2026-03-14)."""
