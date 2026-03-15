"""
Domain error hierarchy. All domain errors must subclass DomainError.
Never raise HTTP-level exceptions from domain code.
"""
from __future__ import annotations
from typing import Any


class DomainError(Exception):
    """Base for all domain errors."""
    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.context = context or {}


class NotFoundError(DomainError):
    """Raised when a required aggregate or value object is not found."""


class ConflictError(DomainError):
    """Raised when an operation conflicts with existing state (optimistic concurrency, duplicate)."""


class ValidationError(DomainError):
    """Raised when a domain invariant is violated."""


class PermissionError(DomainError):
    """Raised when an actor lacks authorization for the requested operation."""


class PreconditionError(DomainError):
    """Raised when an operation's preconditions are not met."""


class StaleAggregateError(ConflictError):
    """Raised when optimistic concurrency version check fails."""
    def __init__(self, aggregate_id: str, expected: int, actual: int) -> None:
        super().__init__(
            f"Stale aggregate {aggregate_id}: expected version {expected}, got {actual}",
            {"aggregate_id": aggregate_id, "expected": expected, "actual": actual},
        )
