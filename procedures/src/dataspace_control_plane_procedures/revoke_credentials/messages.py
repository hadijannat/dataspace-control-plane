from __future__ import annotations

from dataclasses import dataclass

from .input import RevocationStatusQuery


@dataclass(frozen=True)
class ExternalRevocationConfirmed:
    """Signal: async callback from issuer confirming revocation was recorded."""
    event_id: str
    issuer_ref: str


__all__ = ["ExternalRevocationConfirmed", "RevocationStatusQuery"]
