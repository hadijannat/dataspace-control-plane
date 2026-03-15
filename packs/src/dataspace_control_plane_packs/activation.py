"""Pack activation — per-tenant/legal-entity/environment pack binding.

Activation is the concern of deciding which packs are active for a given
runtime scope (tenant, legal entity, environment). It is separate from:
- Pack loading (loader.py) — imports packs at startup
- Pack resolution (resolver.py) — resolves dependency graphs

Activation state is lightweight: a mapping from activation scope key to
a resolved profile. Callers (apps/, procedures/ activities) query activation
to get the ResolvedPackProfile for the current tenant/entity.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from ._shared.errors import PackActivationError
from .registry import PackRegistry
from .resolver import PackResolver, ResolvedPackProfile

logger = logging.getLogger(__name__)

ScopeKind = Literal["tenant", "legal_entity", "environment"]


@dataclass
class ActivationRequest:
    """A request to activate a set of packs for a specific scope."""

    scope_kind: ScopeKind
    scope_id: str
    """The tenant_id, legal_entity_id, or environment name."""

    requested_packs: list[str]
    """Pack IDs to activate."""

    pack_options: dict[str, Any] = field(default_factory=dict)
    """Pack-specific option overrides keyed by pack_id."""


@dataclass
class ActivationState:
    """Stores resolved profiles for all active scopes."""

    _profiles: dict[str, ResolvedPackProfile] = field(default_factory=dict)

    def get(self, scope_key: str) -> ResolvedPackProfile | None:
        """Return the resolved profile for ``scope_key``, or None."""
        return self._profiles.get(scope_key)

    def set(self, scope_key: str, profile: ResolvedPackProfile) -> None:
        self._profiles[scope_key] = profile

    def scope_keys(self) -> list[str]:
        return list(self._profiles.keys())


class PackActivationManager:
    """Manages pack activations across scopes.

    Usage::

        manager = PackActivationManager(registry)
        profile = manager.activate(
            ActivationRequest(
                scope_kind="tenant",
                scope_id="tenant-acme",
                requested_packs=["catenax", "battery_passport"],
            )
        )
    """

    def __init__(self, registry: PackRegistry) -> None:
        self._registry = registry
        self._resolver = PackResolver(registry)
        self._state = ActivationState()

    def activate(self, request: ActivationRequest) -> ResolvedPackProfile:
        """Resolve and cache the pack profile for the given activation request.

        Returns the cached profile if the scope_key is already activated.
        Call ``deactivate`` to force re-resolution.

        Raises:
            PackActivationError: If resolution fails.
        """
        scope_key = f"{request.scope_kind}:{request.scope_id}"
        existing = self._state.get(scope_key)
        if existing is not None:
            return existing

        try:
            self._validate_scope(request)
            profile = self._resolver.resolve(
                activation_id=scope_key,
                requested_packs=request.requested_packs,
                metadata={
                    "scope_kind": request.scope_kind,
                    "scope_id": request.scope_id,
                    "pack_options": request.pack_options,
                },
            )
        except Exception as exc:
            raise PackActivationError(
                f"Failed to activate packs {request.requested_packs} "
                f"for scope {scope_key!r}: {exc}"
            ) from exc

        self._state.set(scope_key, profile)
        logger.info(
            "Activated packs %s for scope %s",
            profile.pack_ids(),
            scope_key,
        )
        return profile

    def deactivate(self, scope_kind: ScopeKind, scope_id: str) -> None:
        """Remove the cached activation for the given scope (forces re-resolution next access)."""
        scope_key = f"{scope_kind}:{scope_id}"
        if scope_key in self._state.scope_keys():
            del self._state._profiles[scope_key]

    def get_profile(self, scope_kind: ScopeKind, scope_id: str) -> ResolvedPackProfile | None:
        """Return the cached resolved profile, or None if not yet activated."""
        return self._state.get(f"{scope_kind}:{scope_id}")

    def _validate_scope(self, request: ActivationRequest) -> None:
        """Check that all requested packs support the requested scope kind."""
        for pack_id in request.requested_packs:
            if not self._registry.has_pack(pack_id):
                continue  # PackNotFoundError will surface in resolver
            manifest = self._registry.manifest(pack_id)
            if manifest.activation_scope != request.scope_kind:
                logger.warning(
                    "Pack %r declares activation_scope=%r but is being activated "
                    "at scope_kind=%r. This may produce unexpected behavior.",
                    pack_id,
                    manifest.activation_scope,
                    request.scope_kind,
                )
