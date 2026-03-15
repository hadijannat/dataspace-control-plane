"""Minimal interceptor contract placeholder for runtime owners."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcedureInterceptor:
    name: str
