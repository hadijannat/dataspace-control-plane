"""Gaia-X data exchange profile provider.

Gaia-X does NOT prescribe a single mandatory data exchange protocol stack.
Authentication and policy negotiation/contracting are mandatory; the
transport protocol is capability-based.
Reference: Gaia-X Data Exchange Services specification.
"""
from __future__ import annotations

from typing import Any

from .._shared.interfaces import DataExchangeProfileProvider


class GaiaXDataExchangeProfileProvider:
    """Capability-based data exchange profile for Gaia-X.

    Mandatory capabilities (all Gaia-X participants):
      - authentication (OIDC/DID-based)
      - policy_negotiation (ODRL is a recommended candidate)

    Supported (not mandated) protocols:
      - dsp, dcp, odrl, oidc

    The absence of a single mandatory protocol is by design: Gaia-X
    explicitly allows federations to add their own protocol requirements
    via federation overlay packs.
    """

    def supported_protocols(self) -> list[str]:
        """Return known protocol identifiers (not all mandatory)."""
        return ["dsp", "dcp", "odrl", "oidc", "https"]

    def required_capabilities(self, *, context: dict[str, Any]) -> list[str]:
        """Return capabilities required for all Gaia-X participants.

        ``authentication`` and ``policy_negotiation`` are always mandatory.
        Additional capabilities may be added by federation overlays.
        """
        return ["authentication", "policy_negotiation"]
