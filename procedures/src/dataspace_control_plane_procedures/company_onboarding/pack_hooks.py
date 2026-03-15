"""Pack-specific branching hooks Protocol for company_onboarding.

Implementations live in ``packs/``, never here. This module only defines
the interface that pack overlays must satisfy.
"""
from __future__ import annotations

from typing import Protocol


class OnboardingPackHooks(Protocol):
    """Pack-specific branching hooks. Implemented by packs/, not here."""

    def extra_phases(self, pack_id: str) -> list[str]:
        """Return additional workflow phases required by this pack."""
        ...

    def requires_bpnl(self, pack_id: str) -> bool:
        """Return True if the pack mandates a BPNL for onboarding."""
        ...

    def approval_endpoint(self, pack_id: str) -> str | None:
        """Return the pack-specific approval submission URL, or None for default."""
        ...
