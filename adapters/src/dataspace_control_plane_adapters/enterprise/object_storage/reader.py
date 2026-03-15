"""Object storage reader — download objects and iterate over keys."""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from .client import s3_client
from .config import ObjectStorageSettings
from .errors import ObjectNotFoundError, ObjectStorageDownloadError, ObjectStorageError

logger = logging.getLogger(__name__)


class ObjectReader:
    """Downloads objects and lists keys from S3-compatible storage."""

    def __init__(self, settings: ObjectStorageSettings) -> None:
        self._settings = settings

    async def get_bytes(self, key: str, *, bucket: str | None = None) -> bytes:
        """Download an object and return its raw bytes.

        Args:
            key: Object key within the bucket.
            bucket: Override the default bucket.

        Raises:
            ObjectNotFoundError: If the key does not exist.
            ObjectStorageDownloadError: On any other S3 error.
        """
        bucket = bucket or self._settings.default_bucket
        async with s3_client(self._settings) as s3:
            try:
                resp = await s3.get_object(Bucket=bucket, Key=key)
                async with resp["Body"] as stream:
                    return await stream.read()
            except Exception as exc:
                err_code = _extract_error_code(exc)
                if err_code in ("NoSuchKey", "404"):
                    raise ObjectNotFoundError(
                        f"Object not found: s3://{bucket}/{key}"
                    ) from exc
                raise ObjectStorageDownloadError(
                    f"Failed to download s3://{bucket}/{key}: {exc}"
                ) from exc

    async def get_text(self, key: str, *, bucket: str | None = None, encoding: str = "utf-8") -> str:
        """Download an object as a decoded string."""
        raw = await self.get_bytes(key, bucket=bucket)
        return raw.decode(encoding)

    async def list_keys(
        self, prefix: str = "", *, bucket: str | None = None
    ) -> AsyncIterator[str]:
        """Yield all object keys under the given prefix.

        Uses paginated ListObjectsV2 for correctness with large buckets.
        """
        bucket = bucket or self._settings.default_bucket
        async with s3_client(self._settings) as s3:
            paginator = s3.get_paginator("list_objects_v2")
            try:
                async for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                    for obj in page.get("Contents") or []:
                        yield obj["Key"]
            except Exception as exc:
                raise ObjectStorageError(
                    f"Failed to list keys with prefix {prefix!r} in {bucket}: {exc}"
                ) from exc

    async def head(self, key: str, *, bucket: str | None = None) -> dict[str, Any]:
        """Return object metadata without downloading the body.

        Returns a dict with ``content_length``, ``content_type``, ``etag``,
        ``last_modified``, and ``metadata`` (user-defined headers).

        Raises:
            ObjectNotFoundError: If the key does not exist.
        """
        bucket = bucket or self._settings.default_bucket
        async with s3_client(self._settings) as s3:
            try:
                resp = await s3.head_object(Bucket=bucket, Key=key)
                return {
                    "content_length": resp.get("ContentLength"),
                    "content_type": resp.get("ContentType"),
                    "etag": resp.get("ETag", "").strip('"'),
                    "last_modified": resp.get("LastModified"),
                    "metadata": resp.get("Metadata") or {},
                }
            except Exception as exc:
                err_code = _extract_error_code(exc)
                if err_code in ("NoSuchKey", "404", "HeadObject"):
                    raise ObjectNotFoundError(
                        f"Object not found: s3://{bucket}/{key}"
                    ) from exc
                raise ObjectStorageDownloadError(
                    f"head_object failed for s3://{bucket}/{key}: {exc}"
                ) from exc


def _extract_error_code(exc: Exception) -> str:
    """Best-effort extraction of the boto error code from an exception."""
    response = getattr(exc, "response", None)
    if isinstance(response, dict):
        return response.get("Error", {}).get("Code", "")
    return type(exc).__name__
