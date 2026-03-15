"""BOM (Bill of Materials) extraction for the Siemens Teamcenter adapter."""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from .client import TeamcenterClient
from .config import TeamcenterSettings
from .errors import TeamcenterNotFoundError


class BomExtractor:
    """Extracts Bill of Materials structures from Teamcenter.

    Uses the Teamcenter StructureManagement microservice to traverse
    product structures. Large structures are fetched in chunks of
    ``settings.chunk_size`` to allow safe resume.
    """

    # Teamcenter StructureManagement service path.
    _STRUCTURE_PATH = "/tc/micro/StructureManagement/BOMWindow"

    def __init__(self, client: TeamcenterClient, settings: TeamcenterSettings) -> None:
        self._client = client
        self._settings = settings

    async def extract_bom(
        self,
        root_item_id: str,
        depth: int = -1,
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield BOM line records for the given root item.

        Args:
            root_item_id: Teamcenter item UID for the root of the BOM.
            depth: Maximum BOM depth to traverse. ``-1`` means unlimited.

        Yields:
            Dicts with keys: ``item_id``, ``parent_id``, ``quantity``,
            ``unit``, ``revision``, ``level``, ``root_item_id``.
        """
        structure = await self.get_structure(root_item_id)
        lines = structure.get("bomLines", [])
        for line in lines:
            yield _normalize_bom_line(line, root_item_id)

    async def get_structure(self, item_id: str) -> dict[str, Any]:
        """Fetch the flat BOM tree for ``item_id`` from Teamcenter.

        Returns the raw StructureManagement response dict with a ``bomLines``
        list. Raises TeamcenterNotFoundError when the item does not exist.
        """
        path = f"{self._STRUCTURE_PATH}/{item_id}"
        try:
            return await self._client.get(path)
        except Exception as exc:
            msg = str(exc)
            if "404" in msg or "not found" in msg.lower():
                raise TeamcenterNotFoundError(
                    f"BOM root item '{item_id}' not found in Teamcenter."
                ) from exc
            raise


def _normalize_bom_line(line: dict[str, Any], root_item_id: str) -> dict[str, Any]:
    """Normalize a raw Teamcenter BOM line to a flat record dict."""
    return {
        "item_id": line.get("itemId") or line.get("uid", ""),
        "parent_id": line.get("parentId") or line.get("parentUid", ""),
        "quantity": _safe_float(line.get("quantity", 1)),
        "unit": line.get("unit") or line.get("unitOfMeasure", "EA"),
        "revision": line.get("revisionId") or line.get("revision", ""),
        "level": int(line.get("level", 0)),
        "root_item_id": root_item_id,
    }


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 1.0
