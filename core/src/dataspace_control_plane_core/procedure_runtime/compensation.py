"""Compensation contracts for reversible procedure steps."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompensationStep:
    action: str
    description: str
    required: bool = True


@dataclass(frozen=True)
class CompensationPlan:
    steps: tuple[CompensationStep, ...] = ()
