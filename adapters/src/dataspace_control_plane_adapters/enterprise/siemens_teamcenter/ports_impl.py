"""Source adapter for Teamcenter that combines BOM + revision + document extraction."""
from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from .bom_extract import BomExtractor
from .client import TeamcenterClient
from .config import TeamcenterSettings
from .document_extract import DocumentExtractor
from .item_revision_extract import ItemRevisionExtractor


class TeamcenterSourceAdapter:
    """Normalizes Teamcenter item data into source records for the schema_mapping pipeline.

    No business logic — combines BOM lines, revision metadata, and linked dataset
    metadata into flat normalized records for downstream mapping.
    """

    def __init__(self, settings: TeamcenterSettings, tenant_id: str) -> None:
        self._settings = settings
        self._tenant_id = tenant_id
        self._client = TeamcenterClient(settings)

    async def extract_records(
        self,
        tenant_id: str,
        item_ids: list[str],
    ) -> AsyncIterator[dict[str, Any]]:
        """Yield normalized source records for the given item IDs.

        Each record is a flat dict combining:
          - BOM line data (item_id, parent_id, quantity, unit, revision, level)
          - Revision metadata (lifecycle_state, effective_date, created_by, modified_date)
          - Dataset list summary (count, names)
          - Source envelope: ``__source``, ``__tenant_id``

        Iterates items in chunks to stay within ``settings.chunk_size`` per request.
        """
        await self._client.login()
        bom_extractor = BomExtractor(self._client, self._settings)
        revision_extractor = ItemRevisionExtractor(self._client)
        doc_extractor = DocumentExtractor(self._client)

        chunk_size = self._settings.chunk_size
        for batch_start in range(0, len(item_ids), chunk_size):
            batch = item_ids[batch_start : batch_start + chunk_size]
            for item_id in batch:
                # Fetch latest revision metadata (first revision returned).
                revisions = await revision_extractor.list_revisions(item_id)
                latest_rev = revisions[0] if revisions else {}
                rev_id = latest_rev.get("rev_id", "")

                # Fetch datasets attached to this revision.
                datasets: list[dict[str, Any]] = []
                if rev_id:
                    try:
                        datasets = await doc_extractor.list_datasets(item_id, rev_id)
                    except Exception:
                        datasets = []

                # Fetch BOM lines under this item as root.
                async for bom_line in bom_extractor.extract_bom(item_id):
                    record: dict[str, Any] = {
                        "__source": "siemens_teamcenter",
                        "__tenant_id": tenant_id,
                        **bom_line,
                        **latest_rev,
                        "dataset_count": len(datasets),
                        "dataset_names": [d["name"] for d in datasets],
                    }
                    yield record
