"""
Money and Currency value objects.
Uses integer minor units to avoid floating-point arithmetic.
"""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Currency:
    """ISO 4217 currency code."""
    code: str  # e.g. "EUR", "USD"

    def __post_init__(self) -> None:
        if len(self.code) != 3 or not self.code.isalpha():
            raise ValueError(f"Invalid ISO 4217 currency code: {self.code!r}")

    def __str__(self) -> str:
        return self.code


@dataclass(frozen=True)
class Money:
    """
    An amount in a specific currency, stored as minor units (cents).
    E.g., EUR 12.50 → Money(amount_minor=1250, currency=Currency("EUR"))
    """
    amount_minor: int
    currency: Currency

    def __post_init__(self) -> None:
        if self.amount_minor < 0:
            raise ValueError("Money amount must be non-negative")

    @classmethod
    def zero(cls, currency: Currency) -> "Money":
        return cls(0, currency)

    def as_decimal(self, minor_unit_factor: int = 100) -> Decimal:
        return Decimal(self.amount_minor) / minor_unit_factor

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError("Cannot add money with different currencies")
        return Money(self.amount_minor + other.amount_minor, self.currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.as_decimal():.2f}"
