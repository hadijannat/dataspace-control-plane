"""Multipart upload support for large objects.

Splits objects larger than ``settings.multipart_threshold_bytes`` into parts
of ``settings.multipart_chunk_bytes`` and uploads them using the S3 multipart
API. Aborts the upload on any failure so partial uploads do not accumulate.
"""
from __future__ import annotations

import logging
import math

from .client import s3_client
from .config import ObjectStorageSettings
from .errors import ObjectStorageUploadError

logger = logging.getLogger(__name__)


class MultipartUploader:
    """Performs S3 multipart upload for large byte payloads."""

    def __init__(self, settings: ObjectStorageSettings) -> None:
        self._settings = settings

    async def upload(
        self,
        *,
        key: str,
        data: bytes,
        bucket: str,
        content_type: str = "application/octet-stream",
        metadata: dict[str, str] | None = None,
    ) -> str:
        """Upload ``data`` using multipart upload. Returns the final ETag.

        Raises:
            ObjectStorageUploadError: If any part or the completion step fails.
        """
        chunk_size = self._settings.multipart_chunk_bytes
        num_parts = math.ceil(len(data) / chunk_size)
        upload_id: str | None = None

        async with s3_client(self._settings) as s3:
            try:
                create_resp = await s3.create_multipart_upload(
                    Bucket=bucket,
                    Key=key,
                    ContentType=content_type,
                    Metadata=metadata or {},
                )
                upload_id = create_resp["UploadId"]

                parts = []
                for i in range(num_parts):
                    part_number = i + 1
                    chunk = data[i * chunk_size : (i + 1) * chunk_size]
                    part_resp = await s3.upload_part(
                        Bucket=bucket,
                        Key=key,
                        UploadId=upload_id,
                        PartNumber=part_number,
                        Body=chunk,
                    )
                    parts.append(
                        {"PartNumber": part_number, "ETag": part_resp["ETag"]}
                    )
                    logger.debug(
                        "Uploaded part %d/%d for s3://%s/%s",
                        part_number,
                        num_parts,
                        bucket,
                        key,
                    )

                complete_resp = await s3.complete_multipart_upload(
                    Bucket=bucket,
                    Key=key,
                    UploadId=upload_id,
                    MultipartUpload={"Parts": parts},
                )
                return complete_resp.get("ETag", "").strip('"')

            except Exception as exc:
                if upload_id is not None:
                    try:
                        await s3.abort_multipart_upload(
                            Bucket=bucket, Key=key, UploadId=upload_id
                        )
                        logger.info("Aborted multipart upload %s for s3://%s/%s", upload_id, bucket, key)
                    except Exception:
                        logger.warning("Failed to abort multipart upload %s", upload_id)
                raise ObjectStorageUploadError(
                    f"Multipart upload failed for s3://{bucket}/{key}: {exc}"
                ) from exc
