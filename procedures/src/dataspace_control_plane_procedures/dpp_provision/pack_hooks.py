"""Pack-specific branching hooks Protocol for dpp_provision.

Implementations live in ``packs/``, never here. This module only defines
the interface that pack overlays must satisfy.
"""
from __future__ import annotations

from typing import Protocol


class DppPackHooks(Protocol):
    """Pack-specific branching hooks. Implemented by packs/, not here."""

    def mandatory_submodel_ids(self, pack_id: str) -> list[str]:
        """Return the list of submodel IDs that are mandatory for this pack."""
        ...

    def identifier_link_service(self, pack_id: str, tenant_id: str) -> str:
        """Return the identifier link service URL for this pack and tenant."""
        ...

    def min_completeness_score(self, pack_id: str) -> float:
        """Return the minimum acceptable completeness score for this pack."""
        ...
