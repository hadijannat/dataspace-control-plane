"""Item Revision metadata extraction for the Siemens Teamcenter adapter."""
from __future__ import annotations

from typing import Any

from .client import TeamcenterClient
from .errors import TeamcenterNotFoundError


class ItemRevisionExtractor:
    """Extracts Item Revision metadata from Teamcenter.

    Uses the Teamcenter Item microservice to retrieve revision lists and
    per-revision metadata including lifecycle state and effective dates.
    """

    _ITEM_PATH = "/tc/micro/ItemManagement/Item"

    def __init__(self, client: TeamcenterClient) -> None:
        self._client = client

    async def get_revision(self, item_id: str, rev_id: str) -> dict[str, Any]:
        """Fetch metadata for a specific item revision.

        Returns a normalized record with:
          ``item_id``, ``rev_id``, ``lifecycle_state``, ``effective_date``,
          ``created_by``, ``modified_date``.

        Raises TeamcenterNotFoundError when the item/revision does not exist.
        """
        path = f"{self._ITEM_PATH}/{item_id}/revision/{rev_id}"
        try:
            raw = await self._client.get(path)
        except Exception as exc:
            msg = str(exc)
            if "404" in msg or "not found" in msg.lower():
                raise TeamcenterNotFoundError(
                    f"Item revision '{item_id}/{rev_id}' not found in Teamcenter."
                ) from exc
            raise
        return _normalize_revision(raw, item_id)

    async def list_revisions(self, item_id: str) -> list[dict[str, Any]]:
        """Return a list of all revisions for the given item.

        Each entry contains the same fields as ``get_revision`` returns.
        Raises TeamcenterNotFoundError when the item does not exist.
        """
        path = f"{self._ITEM_PATH}/{item_id}/revisions"
        try:
            raw = await self._client.get(path)
        except Exception as exc:
            msg = str(exc)
            if "404" in msg or "not found" in msg.lower():
                raise TeamcenterNotFoundError(
                    f"Item '{item_id}' not found in Teamcenter."
                ) from exc
            raise
        revisions = raw.get("revisions") or raw.get("value") or []
        return [_normalize_revision(r, item_id) for r in revisions]


def _normalize_revision(raw: dict[str, Any], item_id: str) -> dict[str, Any]:
    """Normalize a raw Teamcenter revision response to a flat record."""
    return {
        "item_id": raw.get("itemId") or item_id,
        "rev_id": raw.get("revisionId") or raw.get("id", ""),
        "lifecycle_state": raw.get("lifecycleState") or raw.get("releaseStatus", ""),
        "effective_date": raw.get("effectiveDate") or raw.get("dateReleased", ""),
        "created_by": raw.get("createdBy") or raw.get("owningUser", ""),
        "modified_date": raw.get("lastModifiedDate") or raw.get("dateModified", ""),
    }
