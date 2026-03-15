"""Pack-specific branching hooks Protocol for delegate_tenant.

Implementations live in ``packs/``, never here. This module only defines
the interface that pack overlays must satisfy.
"""
from __future__ import annotations

from typing import Protocol


class DelegationPackHooks(Protocol):
    """Pack-specific branching hooks. Implemented by packs/, not here."""

    def requires_cross_border_review(
        self,
        pack_id: str,
        parent_jurisdiction: str,
        child_jurisdiction: str,
    ) -> bool:
        """Return True when cross-border delegation requires manual sign-off."""
        ...

    def max_delegation_depth(self, pack_id: str) -> int:
        """Return the maximum allowed nesting depth of entity delegations for this pack."""
        ...
