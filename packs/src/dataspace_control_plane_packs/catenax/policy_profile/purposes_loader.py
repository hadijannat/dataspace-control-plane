"""Load purposes vocabulary from purposes.yaml."""
from __future__ import annotations

import pathlib

import yaml

_PURPOSES_YAML = pathlib.Path(__file__).parent / "purposes.yaml"

# Module-level cache: the purposes YAML is a static, read-only normative asset
# that never changes at runtime.  Parsing it once avoids repeated file I/O and
# YAML deserialization when multiple CatenaxPurposeCatalogProvider instances are
# created (e.g. in tests that reset the registry).
_PURPOSES_CACHE: dict | None = None


def load_purposes() -> dict:
    global _PURPOSES_CACHE
    if _PURPOSES_CACHE is None:
        with open(_PURPOSES_YAML) as f:
            _PURPOSES_CACHE = yaml.safe_load(f)
    return _PURPOSES_CACHE
