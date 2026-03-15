"""Helpers for converting shared search-attribute definitions to runtime payloads."""
from __future__ import annotations

from typing import Any


def encode_search_attributes(values: dict[str, Any]) -> dict[str, Any]:
    """Return a shallow copy for adapter/runtime serialization."""
    return dict(values)
