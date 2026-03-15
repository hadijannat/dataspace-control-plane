"""Public import surface for the SQL extract adapter."""
from __future__ import annotations

from .cdc_postgres import consume_cdc
from .config import SqlExtractSettings
from .errors import (
    SqlCdcError,
    SqlExtractError,
    SqlIntrospectionError,
    SqlSnapshotError,
    SqlTypeMapError,
    SqlWatermarkError,
)
from .introspection import introspect_table, list_tables
from .ports_impl import SqlExtractPort
from .snapshot import snapshot_table
from .type_mapping import canonical_type, coerce_value
from .watermark import read_max_watermark

__all__ = [
    "SqlExtractSettings",
    "SqlExtractPort",
    "snapshot_table",
    "read_max_watermark",
    "consume_cdc",
    "introspect_table",
    "list_tables",
    "canonical_type",
    "coerce_value",
    "SqlExtractError",
    "SqlIntrospectionError",
    "SqlSnapshotError",
    "SqlWatermarkError",
    "SqlCdcError",
    "SqlTypeMapError",
]
