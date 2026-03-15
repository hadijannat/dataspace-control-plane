"""Public import surface for the object storage adapter."""
from __future__ import annotations

from .client import s3_client
from .config import ObjectStorageSettings
from .digests import md5_hex, sha256_hex, verify_etag, verify_sha256
from .errors import (
    ObjectNotFoundError,
    ObjectStorageChecksumError,
    ObjectStorageDeleteError,
    ObjectStorageDownloadError,
    ObjectStorageError,
    ObjectStorageUploadError,
)
from .multipart import MultipartUploader
from .ports_impl import ObjectStoragePort
from .reader import ObjectReader
from .writer import ObjectWriter

__all__ = [
    "ObjectStorageSettings",
    "ObjectStoragePort",
    "ObjectReader",
    "ObjectWriter",
    "MultipartUploader",
    "s3_client",
    "sha256_hex",
    "md5_hex",
    "verify_sha256",
    "verify_etag",
    "ObjectStorageError",
    "ObjectNotFoundError",
    "ObjectStorageUploadError",
    "ObjectStorageDownloadError",
    "ObjectStorageDeleteError",
    "ObjectStorageChecksumError",
]
