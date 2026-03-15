"""Hash digest primitives for evidence manifests and exports."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass(frozen=True)
class HashDigest:
    algorithm: str
    hex_value: str


_ALLOWED_ALGORITHMS: frozenset[str] = frozenset({"sha256", "sha384", "sha512"})


def digest_bytes(payload: bytes, algorithm: str = "sha256") -> HashDigest:
    if algorithm not in _ALLOWED_ALGORITHMS:
        raise ValueError(
            f"Unsupported digest algorithm '{algorithm}'. "
            f"Allowed: {sorted(_ALLOWED_ALGORITHMS)}"
        )
    hasher = hashlib.new(algorithm)
    hasher.update(payload)
    return HashDigest(algorithm=algorithm, hex_value=hasher.hexdigest())
