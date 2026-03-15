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
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from .errors import NormativeSourceError, PackProvenanceError

PROVENANCE_KEY = "_pack_provenance"

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


def compute_sha256(path: Path) -> str:
    """Return the SHA-256 hex digest of ``path``."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


# Cache: (absolute_path_str, mtime_ns) -> sha256_hex
# Avoids re-hashing large pinned files (e.g. 25k-line HTML) on every
# validate_manifest_sources call when the file has not changed on disk.
_sha256_cache: dict[tuple[str, int], str] = {}


def _compute_sha256_cached(path: Path) -> str:
    """Return the SHA-256 hex digest of ``path``, using an mtime-keyed cache.

    The cache is keyed by ``(str(path), mtime_ns)`` so that any on-disk change
    is detected and the digest is recomputed. This avoids repeatedly reading
    large pinned normative-source files (e.g. 25k-line regulation HTML) during
    startup or test teardown/re-setup cycles.
    """
    key = (str(path), path.stat().st_mtime_ns)
    cached = _sha256_cache.get(key)
    if cached is not None:
        return cached
    digest = compute_sha256(path)
    _sha256_cache[key] = digest
    return digest


def validate_manifest_sources(manifest: Any) -> None:
    """Validate all pinned source files declared by ``manifest``.

    The manifest is expected to expose ``root_dir`` and ``normative_sources``.
    """
    root_dir = Path(manifest.root_dir).resolve()
    for source in manifest.normative_sources:
        local_path = (root_dir / source.local_filename).resolve()
        try:
            local_path.relative_to(root_dir)
        except ValueError as exc:
            raise NormativeSourceError(
                f"Pack {manifest.pack_id!r} declares source {source.local_filename!r} "
                "outside its package root."
            ) from exc

        local_parts = Path(source.local_filename).parts
        allowed_location = (
            len(local_parts) >= 2 and local_parts[0] == "vocab" and local_parts[1] == "pinned"
        ) or ("vendor" in local_parts)
        if not allowed_location:
            raise NormativeSourceError(
                f"Pack {manifest.pack_id!r} source {source.local_filename!r} must live "
                "under vocab/pinned/ or vendor/."
            )
        if not local_path.is_file():
            raise NormativeSourceError(
                f"Pack {manifest.pack_id!r} source file is missing: {source.local_filename!r}"
            )

        actual_sha256 = _compute_sha256_cached(local_path)
        if actual_sha256.lower() != source.sha256.lower():
            raise NormativeSourceError(
                f"Pack {manifest.pack_id!r} source checksum mismatch for "
                f"{source.local_filename!r}: expected {source.sha256}, got {actual_sha256}."
            )


def attach_pack_provenance(
    payload: dict[str, Any],
    *,
    pack_id: str,
    pack_version: str,
    sources: list[NormativeSource],
    rule_ids: list[str],
    activation_scope: str,
) -> dict[str, Any]:
    """Attach or merge pack provenance onto ``payload``.

    The reserved metadata key is ``_pack_provenance``. It stores a stable
    per-pack mapping so multi-pack reducers can preserve every contributing
    provenance record.
    """
    result = dict(payload)
    existing = result.get(PROVENANCE_KEY, {})
    records: dict[str, Any]

    if isinstance(existing, dict) and "records" in existing and isinstance(existing["records"], dict):
        records = dict(existing["records"])
    elif isinstance(existing, dict):
        records = {
            key: value
            for key, value in existing.items()
            if isinstance(value, dict)
        }
    else:
        records = {}

    provenance = ArtifactProvenance.build(
        pack_id=pack_id,
        pack_version=pack_version,
        rule_ids=rule_ids,
        sources=sources,
        activation_scope=activation_scope,
    )
    records[pack_id] = provenance.as_dict()
    result[PROVENANCE_KEY] = {"records": records}
    return result


def require_pack_provenance(payload: dict[str, Any]) -> dict[str, Any]:
    """Raise if ``payload`` does not carry the reserved provenance envelope."""
    provenance = payload.get(PROVENANCE_KEY)
    if not isinstance(provenance, dict):
        raise PackProvenanceError("Artifact is missing _pack_provenance.")
    records = provenance.get("records")
    if not isinstance(records, dict) or not records:
        raise PackProvenanceError("Artifact _pack_provenance.records is empty.")
    return payload


def find_pack_manifest_path(module_file: str) -> Path:
    """Walk upward from ``module_file`` until a pack ``manifest.toml`` is found."""
    current = Path(module_file).resolve()
    for parent in current.parents:
        candidate = parent / "manifest.toml"
        if candidate.is_file():
            return candidate
    raise PackProvenanceError(
        f"Unable to locate pack manifest.toml for module file {module_file!r}."
    )


@lru_cache(maxsize=None)
def _cached_manifest_data(manifest_path: str) -> tuple[str, str, tuple[NormativeSource, ...]]:
    from .manifest import PackManifest

    manifest = PackManifest.from_toml(Path(manifest_path))
    return manifest.pack_id, manifest.version, manifest.normative_sources


def attach_module_provenance(
    payload: dict[str, Any],
    *,
    module_file: str,
    rule_ids: list[str],
    activation_scope: str,
) -> dict[str, Any]:
    """Attach provenance for the pack that owns ``module_file``."""
    manifest_path = find_pack_manifest_path(module_file)
    pack_id, pack_version, sources = _cached_manifest_data(str(manifest_path))
    return attach_pack_provenance(
        payload,
        pack_id=pack_id,
        pack_version=pack_version,
        sources=list(sources),
        rule_ids=rule_ids,
        activation_scope=activation_scope,
    )
