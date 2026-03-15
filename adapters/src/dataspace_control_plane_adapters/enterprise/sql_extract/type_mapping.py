"""Maps PostgreSQL column types to canonical Python/JSON types.

Rules:
- All mappings are conservative: prefer str over unknown for safety.
- UUID columns → str (not UUID objects; callers parse if needed).
- JSON/JSONB → dict (parsed).
- Numeric/decimal → str to avoid float precision loss.
- Timestamps → str (ISO 8601 isoformat).
"""
from __future__ import annotations

from .errors import SqlTypeMapError

# PostgreSQL data_type → canonical JSON type name
_PG_TO_CANONICAL: dict[str, str] = {
    # Integers
    "smallint": "integer",
    "integer": "integer",
    "bigint": "integer",
    "int2": "integer",
    "int4": "integer",
    "int8": "integer",
    # Floats — use "float" but callers should be aware of precision
    "real": "float",
    "double precision": "float",
    "float4": "float",
    "float8": "float",
    # Numeric/decimal — string to avoid precision loss
    "numeric": "string",
    "decimal": "string",
    # Booleans
    "boolean": "boolean",
    "bool": "boolean",
    # Text
    "text": "string",
    "character varying": "string",
    "varchar": "string",
    "character": "string",
    "char": "string",
    "name": "string",
    # Binary
    "bytea": "bytes_base64",
    # UUID
    "uuid": "string",
    # Date/Time — ISO 8601 string
    "date": "string",
    "time without time zone": "string",
    "time with time zone": "string",
    "timestamp without time zone": "string",
    "timestamp with time zone": "string",
    "timestamptz": "string",
    "interval": "string",
    # JSON
    "json": "object",
    "jsonb": "object",
    # Arrays — treat as JSON array
    "ARRAY": "array",
}


def canonical_type(pg_type: str) -> str:
    """Return the canonical type name for a PostgreSQL column type.

    Args:
        pg_type: PostgreSQL data_type string (from information_schema).

    Returns:
        Canonical type name: "integer", "float", "string", "boolean",
        "bytes_base64", "object", "array".

    Raises:
        SqlTypeMapError: If the type is unknown and cannot be mapped.
    """
    normalized = pg_type.lower().strip()
    # Array types appear as "ARRAY" in information_schema
    if normalized == "array" or normalized.endswith("[]"):
        return "array"
    result = _PG_TO_CANONICAL.get(normalized)
    if result is None:
        # Unknown type — default to string with a warning rather than hard fail.
        # This ensures extraction continues for tables with custom/extension types.
        return "string"
    return result


def coerce_value(value: object, pg_type: str) -> object:
    """Coerce a Python value returned by asyncpg to a JSON-serializable form.

    Args:
        value: Value from asyncpg row.
        pg_type: PostgreSQL data_type for this column.

    Returns:
        JSON-serializable Python object.
    """
    if value is None:
        return None

    ctype = canonical_type(pg_type)

    if ctype == "string":
        return str(value)
    if ctype in ("integer", "float", "boolean"):
        return value  # already correct Python primitive
    if ctype == "bytes_base64":
        import base64
        if isinstance(value, (bytes, bytearray, memoryview)):
            return base64.b64encode(bytes(value)).decode("ascii")
        return str(value)
    if ctype == "object":
        if isinstance(value, dict):
            return value
        import json
        return json.loads(str(value))
    if ctype == "array":
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value]

    return str(value)
