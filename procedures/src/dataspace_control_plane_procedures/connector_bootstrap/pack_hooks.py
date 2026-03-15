"""Pack-specific branching hooks Protocol for connector_bootstrap.

Implementations live in ``packs/``, never here. This module only defines
the interface that pack overlays must satisfy.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Protocol


class ConnectorPackHooks(Protocol):
    """Pack-specific branching hooks for connector bootstrapping."""

    def dataspace_registration_endpoint(self, pack_id: str) -> str:
        """Return the pack-specific DSP connector registration URL."""
        ...

    def discovery_verification_timeout(self, pack_id: str) -> timedelta:
        """Return the maximum wait time for discovery verification for this pack."""
        ...
