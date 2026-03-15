"""Pack hook protocol for rotate_credentials.

Packs (Catena-X, Gaia-X, etc.) may override issuer endpoints, credential
type selection, and rotation window policy.  Workflow code calls pack hooks
via activities — never directly — so this module only defines the contract.
"""
from __future__ import annotations

from typing import Protocol


class RotationPackHooks(Protocol):
    """Extension point for ecosystem-specific rotation behaviour."""

    def issuer_endpoint(self, pack_id: str, tenant_id: str) -> str:
        """Return the credential issuer endpoint URL for the given pack and tenant."""
        ...

    def credential_types_to_rotate(self, pack_id: str) -> list[str]:
        """Return the list of credential type URIs that require rotation under this pack."""
        ...

    def rotation_window_days(self, pack_id: str) -> int:
        """Return the look-ahead window (in days) for expiry scanning under this pack."""
        ...
