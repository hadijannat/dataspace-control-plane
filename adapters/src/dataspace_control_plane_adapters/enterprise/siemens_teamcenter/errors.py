"""Error types for the Siemens Teamcenter adapter."""
from __future__ import annotations

from ..._shared.errors import AdapterAuthError, AdapterError, AdapterNotFoundError


class TeamcenterError(AdapterError):
    """Root error for the Siemens Teamcenter adapter."""


class TeamcenterAuthError(AdapterAuthError):
    """Authentication or session failure against Teamcenter."""


class TeamcenterNotFoundError(AdapterNotFoundError):
    """Requested Teamcenter item, revision, or dataset was not found."""
