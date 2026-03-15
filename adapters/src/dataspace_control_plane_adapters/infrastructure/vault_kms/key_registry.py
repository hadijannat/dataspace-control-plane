"""Vault key reference registry.

Maps logical (application-level) key names to Vault Transit key paths.
This registry never stores raw key material — only string path references.

Usage:
    registry = VaultKeyRegistry()
    registry.register("signing-key", "dataspace/signing")
    vault_path = registry.resolve("signing-key")  # "dataspace/signing"
"""
from __future__ import annotations

import threading

from .errors import VaultKeyNotFoundError


class VaultKeyRegistry:
    """In-memory registry mapping logical key names to Vault key paths.

    Thread-safe. All operations are O(1) on the internal dict.

    Invariants:
    - Only path references are stored; no key bytes, no secrets.
    - A logical name may only be registered once; re-registration raises ValueError.
    """

    def __init__(self, transit_mount: str = "transit") -> None:
        self._transit_mount = transit_mount
        self._registry: dict[str, str] = {}
        self._lock = threading.Lock()

    def register(self, logical_name: str, vault_key_path: str) -> None:
        """Register a mapping from *logical_name* to *vault_key_path*.

        Args:
            logical_name:   Application-level key identifier.
            vault_key_path: Key name as registered in the Vault Transit engine.

        Raises:
            ValueError: If *logical_name* is already registered with a different path.
        """
        with self._lock:
            existing = self._registry.get(logical_name)
            if existing is not None and existing != vault_key_path:
                raise ValueError(
                    f"Key {logical_name!r} is already registered as {existing!r}; "
                    f"cannot re-register as {vault_key_path!r}."
                )
            self._registry[logical_name] = vault_key_path

    def resolve(self, logical_name: str) -> str:
        """Return the Vault key path for *logical_name*.

        Args:
            logical_name: Application-level key identifier.

        Returns:
            Vault Transit key path (e.g. ``"dataspace/signing"``).

        Raises:
            VaultKeyNotFoundError: The logical name has not been registered.
        """
        with self._lock:
            path = self._registry.get(logical_name)
        if path is None:
            raise VaultKeyNotFoundError(logical_name, self._transit_mount)
        return path

    def list_registered(self) -> list[str]:
        """Return a sorted list of all registered logical key names."""
        with self._lock:
            return sorted(self._registry.keys())

    def is_registered(self, logical_name: str) -> bool:
        """Return True if *logical_name* has a registered mapping."""
        with self._lock:
            return logical_name in self._registry
