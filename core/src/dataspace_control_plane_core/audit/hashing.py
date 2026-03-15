"""Hash digest primitives for evidence manifests and exports."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class HashDigest:
    algorithm: str
    hex_value: str


def digest_bytes(payload: bytes, algorithm: str = "sha256") -> HashDigest:
    hasher = hashlib.new(algorithm)
    hasher.update(payload)
    return HashDigest(algorithm=algorithm, hex_value=hasher.hexdigest())
