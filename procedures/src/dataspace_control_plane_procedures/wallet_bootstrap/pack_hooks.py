from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class WalletPackHooks(Protocol):
    """Pack-specific hooks that influence wallet bootstrap behaviour."""

    def issuer_endpoint(self, pack_id: str, tenant_id: str) -> str:
        """Return the credential issuer endpoint for the given pack and tenant."""
        ...

    def required_credential_types(self, pack_id: str) -> list[str]:
        """Return the list of credential types required by the pack."""
        ...
