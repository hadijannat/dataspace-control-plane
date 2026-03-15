"""Helpers for deterministic procedure payload handling."""
from __future__ import annotations

import json
from typing import Any


def deterministic_json(value: Any) -> str:
    """Serialize nested payloads with stable key ordering."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
