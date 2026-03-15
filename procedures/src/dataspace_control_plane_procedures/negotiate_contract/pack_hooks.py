"""Pack-specific branching hooks Protocol for negotiate_contract.

Implementations live in ``packs/``, never here. This module only defines
the interface that pack overlays must satisfy.
"""
from __future__ import annotations

from typing import Protocol


class NegotiationPackHooks(Protocol):
    """Pack-specific branching hooks. Implemented by packs/, not here."""

    def negotiation_endpoint(self, pack_id: str, tenant_id: str) -> str:
        """Return the pack-specific connector negotiation endpoint URL."""
        ...

    def policy_validation_mode(self, pack_id: str) -> str:
        """Return the policy validation mode for this pack (e.g. 'strict', 'permissive')."""
        ...
