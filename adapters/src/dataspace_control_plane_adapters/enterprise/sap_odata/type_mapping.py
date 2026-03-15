"""OData EDM type to Python type mapping for the SAP OData adapter."""
from __future__ import annotations

from typing import Any


# Map from OData EDM primitive type name to the target Python type.
EDM_TYPE_MAP: dict[str, type] = {
    "Edm.String": str,
    "Edm.Int16": int,
    "Edm.Int32": int,
    "Edm.Int64": int,
    "Edm.Decimal": float,
    "Edm.Single": float,
    "Edm.Double": float,
    "Edm.DateTime": str,
    "Edm.DateTimeOffset": str,
    "Edm.Date": str,
    "Edm.TimeOfDay": str,
    "Edm.Boolean": bool,
    "Edm.Binary": bytes,
    "Edm.Guid": str,
    "Edm.Byte": int,
    "Edm.SByte": int,
    "Edm.Stream": bytes,
    "Edm.Duration": str,
}


def cast_odata_value(value: Any, edm_type: str) -> Any:
    """Cast a raw OData value to the appropriate Python type.

    Returns the value unchanged when the type is unrecognised or value is None.
    Conversion errors are silently ignored and the raw value is returned so that
    downstream schema validation can surface the problem explicitly.
    """
    if value is None:
        return None
    target = EDM_TYPE_MAP.get(edm_type)
    if target is None:
        # Unknown EDM type — pass through without conversion.
        return value
    if isinstance(value, target):
        return value
    try:
        if target is bytes and isinstance(value, str):
            # OData represents binary as base64; return raw string for upstream handling.
            return value.encode("latin-1")
        if target is bool:
            if isinstance(value, str):
                return value.lower() in {"true", "1", "yes"}
            return bool(value)
        return target(value)
    except (ValueError, TypeError):
        return value
