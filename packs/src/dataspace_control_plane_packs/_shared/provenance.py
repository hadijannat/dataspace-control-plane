"""Provenance tracking for all pack-generated artifacts.

Every artifact produced by a pack (a resolved policy, a twin template, an
evidence bundle, a compliance credential payload) must carry an immutable
provenance record so that auditors can replay and verify the exact normative
bundle that generated it.

This is a data-only module. No HTTP, no persistence.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class NormativeSource:
    """A pinned normative input (specification, regulation text, vocabulary).

    All fields are required. Source assets must be stored under
    ``<pack>/vocab/pinned/`` or ``<pack>/vendor/`` with this metadata embedded
    in the pack's provenance ledger.
    """

    source_uri: str
    """Canonical URI of the normative document (stable, official)."""

    version: str
    """Version or release identifier of the normative document."""

    retrieval_date: str
    """ISO 8601 date on which the asset was fetched and pinned."""

    sha256: str
    """SHA-256 hex digest of the local pinned file."""

    local_filename: str
    """Relative path under the pack's vocab/pinned/ or vendor/ directory."""

    effective_from: str | None = None
    """ISO 8601 date from which this source is effective (legal/regulation only)."""

    effective_to: str | None = None
    """ISO 8601 date until which this source is effective (None = still in force)."""

    upstream_license: str | None = None
    """SPDX license identifier or prose description."""


@dataclass(frozen=True)
class ArtifactProvenance:
    """Immutable provenance record attached to every pack-generated artifact.

    Attach this to any object a pack emits — compiled policies, twin templates,
    evidence bundles, compliance payloads — before returning it to callers.
    """

    pack_id: str
    pack_version: str
    rule_ids: tuple[str, ...]
    source_uris: tuple[str, ...]
    source_versions: tuple[str, ...]
    generated_at: str
    """ISO 8601 UTC timestamp."""
    activation_scope: str
    """The scope that triggered this generation (tenant_id, legal_entity_id, or 'environment')."""
    rule_bundle_hash: str
    """SHA-256 of the sorted rule_ids + source_uris tuple — deterministic fingerprint."""

    @classmethod
    def build(
        cls,
        *,
        pack_id: str,
        pack_version: str,
        rule_ids: list[str],
        sources: list[NormativeSource],
        activation_scope: str,
    ) -> "ArtifactProvenance":
        """Construct and hash a provenance record from its inputs."""
        sorted_rules = tuple(sorted(rule_ids))
        sorted_uris = tuple(s.source_uri for s in sorted(sources, key=lambda s: s.source_uri))
        sorted_versions = tuple(s.version for s in sorted(sources, key=lambda s: s.source_uri))
        bundle = json.dumps(
            {"rules": sorted_rules, "uris": sorted_uris}, sort_keys=True
        ).encode()
        bundle_hash = hashlib.sha256(bundle).hexdigest()
        return cls(
            pack_id=pack_id,
            pack_version=pack_version,
            rule_ids=sorted_rules,
            source_uris=sorted_uris,
            source_versions=sorted_versions,
            generated_at=datetime.now(timezone.utc).isoformat(),
            activation_scope=activation_scope,
            rule_bundle_hash=bundle_hash,
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "pack_version": self.pack_version,
            "rule_ids": list(self.rule_ids),
            "source_uris": list(self.source_uris),
            "source_versions": list(self.source_versions),
            "generated_at": self.generated_at,
            "activation_scope": self.activation_scope,
            "rule_bundle_hash": self.rule_bundle_hash,
        }
