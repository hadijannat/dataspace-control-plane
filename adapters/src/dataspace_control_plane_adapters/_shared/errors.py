"""Shared adapter error hierarchy.

Rules:
- Adapter errors never leak into core/ — translate them at ports_impl.py boundaries.
- Every adapter package has its own errors.py that subclasses these base types.
- The hierarchy mirrors the core/ error hierarchy at the adapter layer.
"""
from __future__ import annotations


class AdapterError(Exception):
    """Root for all adapter-layer errors."""

    def __init__(self, message: str, *, upstream_code: str | int | None = None) -> None:
        super().__init__(message)
        self.upstream_code = upstream_code


class AdapterNotFoundError(AdapterError):
    """Remote resource does not exist (HTTP 404, DB not-found, etc.)."""


class AdapterConflictError(AdapterError):
    """Remote resource already exists or version conflict (HTTP 409, optimistic lock)."""


class AdapterAuthError(AdapterError):
    """Authentication or authorization failure at remote boundary."""


class AdapterTimeoutError(AdapterError):
    """Request to remote system timed out."""


class AdapterUnavailableError(AdapterError):
    """Remote system is temporarily unavailable (HTTP 503, connection refused)."""


class AdapterValidationError(AdapterError):
    """Response from remote system failed schema/contract validation."""


class AdapterSerdeError(AdapterError):
    """Failed to serialize or deserialize a remote payload."""


class AdapterConfigError(AdapterError):
    """Adapter misconfiguration detected at startup or first use."""
