"""Catena-X purpose catalog provider.

Serves the purposes declared in policy_profile/purposes.yaml to callers
who need to enumerate or resolve Catena-X usage purposes.

All cx-policy:* IDs are contained within this package — they do not
propagate to core/ or other layers.
"""
from __future__ import annotations

from typing import Any

from .policy_profile.purposes_loader import load_purposes


class CatenaxPurposeCatalogProvider:
    """PurposeCatalogProvider backed by purposes.yaml."""

    def __init__(self) -> None:
        self._data: dict[str, Any] | None = None

    def _load(self) -> dict[str, Any]:
        if self._data is None:
            self._data = load_purposes()
        return self._data

    def purposes(self) -> list[dict[str, Any]]:
        """Return all declared Catena-X purposes."""
        return list(self._load().get("purposes", []))

    def resolve_purpose(self, purpose_id: str) -> dict[str, Any] | None:
        """Return the purpose definition matching ``purpose_id``, or None."""
        for purpose in self.purposes():
            if purpose.get("id") == purpose_id:
                return purpose
        return None
