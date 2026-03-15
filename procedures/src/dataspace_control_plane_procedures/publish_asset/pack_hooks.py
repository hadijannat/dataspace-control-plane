from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class PublishPackHooks(Protocol):
    """Pack-specific hooks that influence asset publication behaviour."""

    def catalog_endpoint(self, pack_id: str) -> str:
        """Return the catalog endpoint URL for the given pack."""
        ...

    def required_policy_dialect(self, pack_id: str) -> str:
        """Return the required DSP policy dialect for the given pack."""
        ...
