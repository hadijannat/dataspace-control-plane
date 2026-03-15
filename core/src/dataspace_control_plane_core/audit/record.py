"""Deprecated compatibility facade. Prefer ``audit.records``."""
from .records import AuditCategory, AuditOutcome, AuditRecord

__all__ = [
    "AuditCategory",
    "AuditOutcome",
    "AuditRecord",
]
