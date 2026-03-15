"""Shared authentication helpers used by HTTP-based adapters.

Each adapter should use these helpers rather than rolling its own token logic.
Key management lives in infrastructure/vault_kms/; this module only assembles
headers/tokens from already-fetched material.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class BearerToken:
    token: str
    header_name: str = "Authorization"

    def as_header(self) -> dict[str, str]:
        return {self.header_name: f"Bearer {self.token}"}


@dataclass(frozen=True)
class ApiKeyToken:
    token: str
    header_name: str = "X-Api-Key"

    def as_header(self) -> dict[str, str]:
        return {self.header_name: self.token}


@runtime_checkable
class TokenProvider(Protocol):
    """Async token provider used by HTTP client wrappers."""

    async def get_token(self) -> str:
        """Return a fresh or cached token string. Never returns expired tokens."""
        ...


class StaticTokenProvider:
    """Token provider backed by a static secret (suitable for M2M API keys)."""

    def __init__(self, token: str) -> None:
        self._token = token

    async def get_token(self) -> str:
        return self._token
