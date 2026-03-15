"""BaSyx-specific error types.

All BaSyx errors subclass adapter-layer base types from _shared/errors.py.
"""
from __future__ import annotations

from ..._shared.errors import AdapterError, AdapterNotFoundError


class BasYxError(AdapterError):
    """Root for all BaSyx adapter errors."""


class AasDescriptorNotFoundError(AdapterNotFoundError):
    """The requested AAS Shell Descriptor does not exist in the registry."""


class SubmodelNotFoundError(AdapterNotFoundError):
    """The requested Submodel Descriptor or Submodel does not exist."""
