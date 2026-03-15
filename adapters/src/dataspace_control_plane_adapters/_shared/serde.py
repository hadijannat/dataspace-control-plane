"""Serialization / deserialization helpers shared across adapters.

Rules:
- Raw vendor JSON/bytes → typed raw_models (done here, not in mappers.py).
- Canonical models → wire format is done in individual mappers.py files.
- Never produce or consume domain aggregates here.
"""
from __future__ import annotations

import json
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from .errors import AdapterSerdeError, AdapterValidationError

M = TypeVar("M", bound=BaseModel)


def parse_json_bytes(data: bytes, encoding: str = "utf-8") -> Any:
    """Decode raw bytes to a Python object. Raises AdapterSerdeError on failure."""
    try:
        return json.loads(data.decode(encoding))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise AdapterSerdeError(f"JSON decode failed: {exc}") from exc


def parse_model(model_cls: type[M], data: Any) -> M:
    """Parse raw dict/JSON into a Pydantic raw_model. Raises AdapterValidationError."""
    try:
        return model_cls.model_validate(data)
    except ValidationError as exc:
        raise AdapterValidationError(
            f"Validation failed for {model_cls.__name__}: {exc}"
        ) from exc


def dump_model(model: BaseModel, *, exclude_none: bool = True) -> dict:
    """Serialize a Pydantic model to a plain dict for wire transmission."""
    return model.model_dump(exclude_none=exclude_none)


def to_json_bytes(obj: Any) -> bytes:
    """Serialize a dict or Pydantic model to JSON bytes."""
    if isinstance(obj, BaseModel):
        return obj.model_dump_json().encode()
    return json.dumps(obj).encode()
