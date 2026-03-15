"""Object storage writer — upload and delete objects."""
from __future__ import annotations

import logging

from .client import s3_client
from .config import ObjectStorageSettings
from .errors import ObjectStorageDeleteError, ObjectStorageUploadError
from .multipart import MultipartUploader

logger = logging.getLogger(__name__)


class ObjectWriter:
    """Uploads and deletes objects in S3-compatible storage.

    Automatically selects multipart upload for objects larger than
    ``settings.multipart_threshold_bytes``.
    """

    def __init__(self, settings: ObjectStorageSettings) -> None:
        self._settings = settings

    async def put_bytes(
        self,
        key: str,
        data: bytes,
        *,
        bucket: str | None = None,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload raw bytes to object storage.

        Returns:
            ETag of the uploaded object.

        Raises:
            ObjectStorageUploadError: If the upload fails.
        """
        bucket = bucket or self._settings.default_bucket

        if len(data) >= self._settings.multipart_threshold_bytes:
            uploader = MultipartUploader(self._settings)
            return await uploader.upload(
                key=key,
                data=data,
                bucket=bucket,
                content_type=content_type,
                metadata=metadata,
            )

        async with s3_client(self._settings) as s3:
            try:
                resp = await s3.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=data,
                    ContentType=content_type,
                    Metadata=metadata or {},
                )
                return resp.get("ETag", "").strip('"')
            except Exception as exc:
                raise ObjectStorageUploadError(
                    f"Failed to upload s3://{bucket}/{key}: {exc}"
                ) from exc

    async def put_text(
        self,
        key: str,
        text: str,
        *,
        bucket: str | None = None,
        encoding: str = "utf-8",
        content_type: str = "text/plain; charset=utf-8",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Encode ``text`` and upload as an object. Returns the ETag."""
        return await self.put_bytes(
            key,
            text.encode(encoding),
            bucket=bucket,
            content_type=content_type,
            metadata=metadata,
        )

    async def delete(self, key: str, *, bucket: str | None = None) -> None:
        """Delete an object from storage.

        Raises:
            ObjectStorageDeleteError: If the deletion fails.
        """
        bucket = bucket or self._settings.default_bucket
        async with s3_client(self._settings) as s3:
            try:
                await s3.delete_object(Bucket=bucket, Key=key)
            except Exception as exc:
                raise ObjectStorageDeleteError(
                    f"Failed to delete s3://{bucket}/{key}: {exc}"
                ) from exc

    async def delete_many(self, keys: list[str], *, bucket: str | None = None) -> list[str]:
        """Batch-delete up to 1000 objects. Returns list of failed keys.

        Uses S3 delete_objects (batch API) for efficiency.
        """
        bucket = bucket or self._settings.default_bucket
        if not keys:
            return []
        objects = [{"Key": k} for k in keys[:1000]]
        async with s3_client(self._settings) as s3:
            try:
                resp = await s3.delete_objects(
                    Bucket=bucket, Delete={"Objects": objects, "Quiet": False}
                )
                return [e["Key"] for e in resp.get("Errors") or []]
            except Exception as exc:
                raise ObjectStorageDeleteError(
                    f"Batch delete failed in bucket {bucket}: {exc}"
                ) from exc
