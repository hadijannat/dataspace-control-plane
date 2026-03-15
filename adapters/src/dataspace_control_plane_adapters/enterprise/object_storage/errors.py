"""Error types for the object storage adapter."""
from __future__ import annotations

from ..._shared.errors import AdapterError, AdapterNotFoundError


class ObjectStorageError(AdapterError):
    """Root error for the object storage adapter."""


class ObjectNotFoundError(AdapterNotFoundError):
    """The requested object key does not exist in the bucket."""


class ObjectStorageUploadError(ObjectStorageError):
    """Failed to upload an object or multipart part."""


class ObjectStorageDownloadError(ObjectStorageError):
    """Failed to download an object."""


class ObjectStorageDeleteError(ObjectStorageError):
    """Failed to delete an object."""


class ObjectStorageChecksumError(ObjectStorageError):
    """Object checksum/digest verification failed."""
