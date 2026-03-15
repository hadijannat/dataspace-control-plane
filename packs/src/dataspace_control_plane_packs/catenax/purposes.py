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
        self._purposes: list[dict[str, Any]] | None = None
        self._purposes_by_id: dict[str, dict[str, Any]] | None = None

    def _load(self) -> None:
        if self._purposes is None:
            data = load_purposes()
            self._purposes = data.get("purposes", [])
            # Build an O(1) lookup index so resolve_purpose is not O(n).
            self._purposes_by_id = {
                p["id"]: p for p in self._purposes if "id" in p
            }

    def purposes(self) -> list[dict[str, Any]]:
        """Return all declared Catena-X purposes."""
        self._load()
        return list(self._purposes)  # type: ignore[arg-type]

    def resolve_purpose(self, purpose_id: str) -> dict[str, Any] | None:
        """Return the purpose definition matching ``purpose_id``, or None."""
        self._load()
        return self._purposes_by_id.get(purpose_id)  # type: ignore[union-attr]
