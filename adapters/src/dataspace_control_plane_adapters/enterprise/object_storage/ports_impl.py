"""Object storage adapter port implementations.

Provides a unified read/write/list interface over S3-compatible storage,
used by procedures/ activities for asset binary storage and DPP artefact
persistence.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from .config import ObjectStorageSettings
from .digests import sha256_hex, verify_sha256
from .errors import ObjectStorageChecksumError, ObjectStorageError
from .reader import ObjectReader
from .writer import ObjectWriter

logger = logging.getLogger(__name__)


class ObjectStoragePort:
    """Implements the core object storage port.

    Callers (procedures/ activities) use this to:
    - Store large binary artefacts (twin submodels, DPP payloads, exports).
    - Read back artefacts by key.
    - List keys for a given prefix.
    - Verify integrity with SHA-256 on download.

    All keys are treated as opaque strings; bucketing logic lives here.
    """

    def __init__(self, settings: ObjectStorageSettings) -> None:
        self._settings = settings
        self._reader = ObjectReader(settings)
        self._writer = ObjectWriter(settings)

    async def store(
        self,
        key: str,
        data: bytes,
        *,
        bucket: str | None = None,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """Upload ``data`` and return ``{key, etag, sha256}`` provenance dict.

        Args:
            key: Target object key.
            data: Raw bytes to store.
            bucket: Bucket override; defaults to settings.default_bucket.
            content_type: MIME type stored as object content-type.
            metadata: User-defined string metadata (key=value).

        Returns:
            Dict with ``key``, ``etag``, ``sha256``.
        """
        etag = await self._writer.put_bytes(
            key, data, bucket=bucket, content_type=content_type, metadata=metadata
        )
        digest = sha256_hex(data)
        return {"key": key, "etag": etag, "sha256": digest}

    async def retrieve(
        self,
        key: str,
        *,
        bucket: str | None = None,
        expected_sha256: str | None = None,
    ) -> bytes:
        """Download an object and optionally verify its SHA-256.

        Args:
            key: Object key to download.
            bucket: Bucket override.
            expected_sha256: If provided, raises ObjectStorageChecksumError on mismatch.

        Returns:
            Raw bytes of the object.
        """
        data = await self._reader.get_bytes(key, bucket=bucket)
        if expected_sha256:
            verify_sha256(data, expected_sha256)
        return data

    def list_keys(
        self, prefix: str = "", *, bucket: str | None = None
    ) -> AsyncIterator[str]:
        """Async iterator over all keys under ``prefix``."""
        return self._reader.list_keys(prefix, bucket=bucket)

    async def head(self, key: str, *, bucket: str | None = None) -> dict[str, Any]:
        """Return object metadata without downloading."""
        return await self._reader.head(key, bucket=bucket)

    async def delete(self, key: str, *, bucket: str | None = None) -> None:
        """Delete a single object."""
        await self._writer.delete(key, bucket=bucket)

    async def delete_many(self, keys: list[str], *, bucket: str | None = None) -> list[str]:
        """Batch-delete up to 1000 keys. Returns failed keys."""
        return await self._writer.delete_many(keys, bucket=bucket)
