"""Error types for the SAP OData adapter."""
from __future__ import annotations

from ..._shared.errors import AdapterError


class SapOdataError(AdapterError):
    """Root error for the SAP OData adapter."""


class ODataMetadataError(SapOdataError):
    """Failed to fetch or parse OData $metadata."""


class ODataQueryError(SapOdataError):
    """Failed to build or execute an OData query."""
