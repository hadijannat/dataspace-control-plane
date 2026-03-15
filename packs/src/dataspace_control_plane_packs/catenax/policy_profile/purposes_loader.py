"""Load purposes vocabulary from purposes.yaml."""
from __future__ import annotations

import pathlib

import yaml

_PURPOSES_YAML = pathlib.Path(__file__).parent / "purposes.yaml"


def load_purposes() -> dict:
    with open(_PURPOSES_YAML) as f:
        return yaml.safe_load(f)
