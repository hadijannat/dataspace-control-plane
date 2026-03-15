"""Linked document and dataset extraction for the Siemens Teamcenter adapter."""
from __future__ import annotations

from typing import Any

import httpx

from .client import TeamcenterClient
from .errors import TeamcenterNotFoundError


class DocumentExtractor:
    """Extracts linked datasets and downloads their content from Teamcenter.

    Uses the Teamcenter Dataset microservice to list and retrieve files
    attached to a given item revision.
    """

    _DATASET_PATH = "/tc/micro/DatasetManagement/Dataset"
    _REVISION_DATASETS_PATH = "/tc/micro/ItemManagement/Item/{item_id}/revision/{rev_id}/datasets"

    def __init__(self, client: TeamcenterClient) -> None:
        self._client = client

    async def list_datasets(self, item_id: str, rev_id: str) -> list[dict[str, Any]]:
        """Return a list of dataset metadata records attached to a revision.

        Each entry contains: ``dataset_id``, ``name``, ``type``, ``mime_type``,
        ``created_by``, ``modified_date``.
        """
        path = self._REVISION_DATASETS_PATH.format(item_id=item_id, rev_id=rev_id)
        try:
            raw = await self._client.get(path)
        except Exception as exc:
            msg = str(exc)
            if "404" in msg or "not found" in msg.lower():
                raise TeamcenterNotFoundError(
                    f"No datasets found for item '{item_id}' revision '{rev_id}'."
                ) from exc
            raise
        datasets = raw.get("datasets") or raw.get("value") or []
        return [_normalize_dataset(d) for d in datasets]

    async def download_dataset(self, dataset_id: str) -> tuple[bytes, str]:
        """Download the content of a dataset by its UID.

        Returns ``(content_bytes, mime_type)``.
        Raises TeamcenterNotFoundError when the dataset does not exist.
        """
        # First resolve the download ticket/URL from the service.
        ticket_path = f"{self._DATASET_PATH}/{dataset_id}/ticket"
        try:
            ticket_resp = await self._client.get(ticket_path)
        except Exception as exc:
            msg = str(exc)
            if "404" in msg or "not found" in msg.lower():
                raise TeamcenterNotFoundError(
                    f"Dataset '{dataset_id}' not found in Teamcenter."
                ) from exc
            raise

        download_url: str = ticket_resp.get("url") or ticket_resp.get("ticket", "")
        mime_type: str = ticket_resp.get("mimeType") or "application/octet-stream"

        if not download_url:
            # Fallback: try a direct binary GET if no ticket URL is provided.
            download_url = f"{self._DATASET_PATH}/{dataset_id}/content"

        # Download the raw file content from the resolved URL.
        async with httpx.AsyncClient(timeout=120.0) as http_client:
            resp = await http_client.get(download_url)
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", mime_type)
            return resp.content, content_type


def _normalize_dataset(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw Teamcenter dataset record to a flat metadata dict."""
    return {
        "dataset_id": raw.get("datasetId") or raw.get("uid", ""),
        "name": raw.get("name") or raw.get("datasetName", ""),
        "type": raw.get("datasetType") or raw.get("type", ""),
        "mime_type": raw.get("mimeType") or "application/octet-stream",
        "created_by": raw.get("createdBy") or raw.get("owningUser", ""),
        "modified_date": raw.get("lastModifiedDate") or raw.get("dateModified", ""),
    }
