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

import hashlib
import json
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

    compatibility_context: dict[str, Any] = field(default_factory=dict)
    """Optional layer-version metadata used for manifest compatibility checks."""


@dataclass
class CachedActivation:
    fingerprint: str
    profile: ResolvedPackProfile


@dataclass
class ActivationState:
    """Stores resolved profiles for all active scopes."""

    _profiles: dict[str, CachedActivation] = field(default_factory=dict)

    def get(self, scope_key: str) -> CachedActivation | None:
        """Return the resolved profile for ``scope_key``, or None."""
        return self._profiles.get(scope_key)

    def set(self, scope_key: str, cached: CachedActivation) -> None:
        self._profiles[scope_key] = cached

    def delete(self, scope_key: str) -> None:
        """Remove the cached activation for ``scope_key`` if present."""
        self._profiles.pop(scope_key, None)

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

    @staticmethod
    def _make_scope_key(scope_kind: str, scope_id: str) -> str:
        """Build a collision-resistant cache key for a (scope_kind, scope_id) pair.

        Using a simple ``f"{scope_kind}:{scope_id}"`` string is unsafe: a
        ``scope_id`` value of ``"legal_entity:acme"`` combined with
        ``scope_kind="tenant"`` produces ``"tenant:legal_entity:acme"``, which is
        indistinguishable from ``scope_kind="tenant:legal_entity"``,
        ``scope_id="acme"`` — a cross-tenant cache collision.

        The SHA-256 digest of the JSON-serialised pair is used instead:
        - Collision-resistant across all (scope_kind, scope_id) combinations.
        - Avoids leaking raw tenant identifiers in cache introspection or logs.
        """
        encoded = json.dumps(
            {"scope_kind": scope_kind, "scope_id": scope_id}, sort_keys=True
        ).encode()
        return hashlib.sha256(encoded).hexdigest()

    def activate(self, request: ActivationRequest) -> ResolvedPackProfile:
        """Resolve and cache the pack profile for the given activation request.

        Returns the cached profile if the scope_key is already activated with
        the same fingerprint.  Call ``deactivate`` to force re-resolution.

        Raises:
            PackActivationError: If resolution fails.
        """
        scope_key = self._make_scope_key(request.scope_kind, request.scope_id)
        fingerprint = self._fingerprint_request(request)
        existing = self._state.get(scope_key)
        if existing is not None and existing.fingerprint == fingerprint:
            return existing.profile

        try:
            self._validate_scope(request)
            metadata = {
                "scope_kind": request.scope_kind,
                "scope_id": request.scope_id,
                "pack_options": request.pack_options,
                **request.compatibility_context,
            }
            profile = self._resolver.resolve(
                activation_id=scope_key,
                requested_packs=request.requested_packs,
                metadata=metadata,
            )
        except Exception as exc:
            raise PackActivationError(
                f"Failed to activate packs {request.requested_packs} "
                f"for scope_kind={request.scope_kind!r}, scope_id=<redacted>: {exc}"
            ) from exc

        self._state.set(scope_key, CachedActivation(fingerprint=fingerprint, profile=profile))
        logger.info(
            "Activated packs %s for scope_kind=%s",
            profile.pack_ids(),
            request.scope_kind,
        )
        return profile

    def deactivate(self, scope_kind: ScopeKind, scope_id: str) -> None:
        """Remove the cached activation for the given scope (forces re-resolution next access)."""
        scope_key = self._make_scope_key(scope_kind, scope_id)
        self._state.delete(scope_key)

    def get_profile(self, scope_kind: ScopeKind, scope_id: str) -> ResolvedPackProfile | None:
        """Return the cached resolved profile, or None if not yet activated."""
        cached = self._state.get(self._make_scope_key(scope_kind, scope_id))
        return cached.profile if cached is not None else None

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

    @staticmethod
    def _fingerprint_request(request: ActivationRequest) -> str:
        payload = {
            "scope_kind": request.scope_kind,
            "scope_id": request.scope_id,
            "requested_packs": sorted(request.requested_packs),
            "pack_options": request.pack_options,
            "compatibility_context": request.compatibility_context,
        }
        encoded = json.dumps(payload, sort_keys=True, default=str).encode()
        return hashlib.sha256(encoded).hexdigest()
