"""Public import surface for the object storage adapter."""
from __future__ import annotations

from .client import s3_client
from .config import ObjectStorageSettings
from .errors import (
    ObjectNotFoundError,
    ObjectStorageChecksumError,
    ObjectStorageDeleteError,
    ObjectStorageDownloadError,
    ObjectStorageError,
    ObjectStorageUploadError,
)
from .health import ObjectStorageHealthProbe
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
    "ObjectStorageHealthProbe",
    "s3_client",
    "ObjectStorageError",
    "ObjectNotFoundError",
    "ObjectStorageUploadError",
    "ObjectStorageDownloadError",
    "ObjectStorageDeleteError",
    "ObjectStorageChecksumError",
]
