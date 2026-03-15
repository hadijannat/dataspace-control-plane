"""Domain errors for the twins domain."""
from __future__ import annotations

from dataspace_control_plane_core.domains._shared.errors import (
    DomainError,
    NotFoundError,
    ConflictError,
)


class TwinNotFoundError(NotFoundError):
    """Raised when a TwinAsset cannot be located by ID or global_asset_id."""


class DuplicateTwinError(ConflictError):
    """Raised when a twin with the same global_asset_id already exists for a tenant."""


class TwinNotPublishedError(DomainError):
    """Raised when an operation requires the twin to be published but it is not."""


class TwinEndpointUnreachableError(DomainError):
    """Raised when a probed endpoint is not reachable."""
