"""Catena-X BPN (Business Partner Number) identifier scheme.

BPN structure:
  BPNL = legal entity   (16 chars: BPN + L + 12 alphanumeric)
  BPNS = site           (16 chars: BPN + S + 12 alphanumeric)
  BPNA = address        (16 chars: BPN + A + 12 alphanumeric)

Reference: Catena-X Operating Model v4.0
"""
from __future__ import annotations

import re

_BPN_PATTERN = re.compile(r"^BPN[LSA][A-Z0-9]{12}$")
_BPNL_PATTERN = re.compile(r"^BPNL[A-Z0-9]{12}$")
_BPNS_PATTERN = re.compile(r"^BPNS[A-Z0-9]{12}$")
_BPNA_PATTERN = re.compile(r"^BPNA[A-Z0-9]{12}$")


class BpnValidator:
    """Validates BPN identifiers against the Catena-X BPN specification."""

    @staticmethod
    def is_valid_bpn(s: str) -> bool:
        """Return True if ``s`` matches the generic BPN pattern (BPNL, BPNS, or BPNA)."""
        return bool(_BPN_PATTERN.match(s))


class BpnlSchemeProvider:
    """Identifier scheme provider for BPNL (legal entity) identifiers."""

    scheme_id: str = "bpnl"

    def validate(self, value: str) -> bool:
        """Return True if ``value`` is a valid BPNL identifier."""
        return bool(_BPNL_PATTERN.match(value.upper()))

    def normalize(self, value: str) -> str:
        """Return the canonical normalized form (uppercased)."""
        return value.upper()


class BpnsSchemeProvider:
    """Identifier scheme provider for BPNS (site) identifiers."""

    scheme_id: str = "bpns"

    def validate(self, value: str) -> bool:
        """Return True if ``value`` is a valid BPNS identifier."""
        return bool(_BPNS_PATTERN.match(value.upper()))

    def normalize(self, value: str) -> str:
        """Return the canonical normalized form (uppercased)."""
        return value.upper()


class BpnaSchemeProvider:
    """Identifier scheme provider for BPNA (address) identifiers."""

    scheme_id: str = "bpna"

    def validate(self, value: str) -> bool:
        """Return True if ``value`` is a valid BPNA identifier."""
        return bool(_BPNA_PATTERN.match(value.upper()))

    def normalize(self, value: str) -> str:
        """Return the canonical normalized form (uppercased)."""
        return value.upper()


def extract_bpn_kind(bpn: str) -> str:
    """Return the kind of BPN identifier.

    Returns:
        ``"legal_entity"`` for BPNL, ``"site"`` for BPNS, ``"address"`` for BPNA.

    Raises:
        ValueError: If ``bpn`` is not a valid BPN identifier.
    """
    normalized = bpn.upper()
    if not BpnValidator.is_valid_bpn(normalized):
        raise ValueError(f"Invalid BPN identifier: {bpn!r}")
    kind_char = normalized[3]
    return {
        "L": "legal_entity",
        "S": "site",
        "A": "address",
    }[kind_char]
