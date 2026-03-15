"""Common Pydantic base types shared across canonical models."""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict


class CanonicalBase(BaseModel):
    """
    Base for all canonical models.
    Frozen (immutable), extra fields forbidden.
    """
    model_config = ConfigDict(frozen=True, extra="forbid")
