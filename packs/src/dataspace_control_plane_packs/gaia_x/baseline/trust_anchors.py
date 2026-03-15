"""Gaia-X baseline trust anchor overlay.

Provides a data-driven trust anchor configuration and the
:class:`TrustAnchorOverlayProvider` implementation.

Design: The baseline overlay makes no network calls and contains no
hard-coded DID values.  It selects a subset of base anchors by comparing
DIDs against a configured allow-list.  By default (empty config) all base
anchors pass through — this models the open Gaia-X baseline posture where
any AISBL-recognised anchor is acceptable.

Federation-specific overlays in ``federations/<id>/`` should override
:meth:`GaiaXBaselineTrustAnchorOverlay.overlay_anchors` to restrict the set.

Security note: ``TrustAnchorConfig.from_file`` verifies the SHA-256 digest of
the pinned trust-anchor file before parsing it.  If the file is absent or its
digest does not match the declared value, loading fails with a
``NormativeSourceError`` rather than silently falling back to an open posture.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..._shared.errors import NormativeSourceError

_GX_PACK_VERSION = "22.10.0"
_DEFAULT_TRUST_ANCHOR_FILE = (
    Path(__file__).resolve().parents[1] / "vocab" / "pinned" / "trust_anchors_22_10.json"
)

# SHA-256 digest of the pinned trust_anchors_22_10.json as declared in manifest.toml.
# This value is the authoritative check — if the file content changes, this must
# be updated in lockstep with manifest.toml[[normative_sources]].
_DEFAULT_TRUST_ANCHOR_SHA256 = (
    "aabc6b5a5e4d565cb2aef38bbb10ab6f81d30fd73f474de9d186a510bb94e144"
)


def _verify_file_sha256(path: Path, expected_hex: str) -> None:
    """Raise ``NormativeSourceError`` if ``path`` does not match ``expected_hex``."""
    hasher = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hasher.update(chunk)
    actual = hasher.hexdigest().lower()
    if actual != expected_hex.lower():
        raise NormativeSourceError(
            f"Trust anchor file {path!r} failed integrity check: "
            f"expected sha256={expected_hex!r}, got {actual!r}. "
            "The file may have been tampered with or is out of date. "
            "Re-pin the file and update manifest.toml and _DEFAULT_TRUST_ANCHOR_SHA256."
        )


@dataclass(frozen=True)
class TrustAnchor:
    """A Gaia-X trust anchor entry.

    Attributes:
        did:            Decentralised Identifier of this anchor.
        name:           Human-readable name.
        public_key_pem: PEM-encoded public key (may be placeholder if not pinned).
        active:         Whether this anchor is currently active.
        federation_id:  Federation this anchor belongs to, or ``None`` for global.
    """

    did: str
    name: str
    public_key_pem: str
    active: bool = True
    federation_id: str | None = None


@dataclass
class TrustAnchorConfig:
    """Configuration holding a list of trust anchors for a deployment.

    Attributes:
        anchors: List of :class:`TrustAnchor` entries.
        version: Version label for this configuration snapshot.
    """

    anchors: list[TrustAnchor] = field(default_factory=list)
    version: str = "22.10"

    def active_anchors(self) -> list[TrustAnchor]:
        """Return only anchors with ``active=True``."""
        return [a for a in self.anchors if a.active]

    def anchors_for_federation(self, federation_id: str) -> list[TrustAnchor]:
        """Return active anchors for a specific federation."""
        return [
            a for a in self.active_anchors()
            if a.federation_id == federation_id
        ]

    @classmethod
    def from_file(
        cls,
        path: Path,
        *,
        expected_sha256: str | None = None,
    ) -> "TrustAnchorConfig":
        """Load a trust anchor config snapshot from a pinned JSON file.

        Args:
            path:            Path to the pinned JSON file.
            expected_sha256: Expected SHA-256 hex digest of the file.  When
                             provided, the file is checked before parsing.
                             Pass ``None`` only in tests with synthetic data.

        Raises:
            NormativeSourceError: If the file is missing or the digest does not
                match ``expected_sha256``.
        """
        if not path.is_file():
            raise NormativeSourceError(
                f"Pinned trust anchor file is missing: {path!r}. "
                "The file must exist — there is no safe fallback posture when "
                "the trust anchor snapshot is absent."
            )

        if expected_sha256 is not None:
            _verify_file_sha256(path, expected_sha256)

        with path.open() as handle:
            payload = json.load(handle)

        anchors = [
            TrustAnchor(
                did=item["did"],
                name=item["name"],
                public_key_pem=item.get("public_key_pem", ""),
                active=item.get("active", True),
                federation_id=item.get("federation_id"),
            )
            for item in payload.get("anchors", [])
        ]
        return cls(
            anchors=anchors,
            version=payload.get("version", "22.10"),
        )


class GaiaXBaselineTrustAnchorOverlay:
    """Baseline trust anchor overlay for Gaia-X.

    Implements :class:`TrustAnchorOverlayProvider`.

    The baseline policy is permissive: any anchor in ``base_anchors`` passes
    through unless a local config restricts the allowed DID set.  Federation
    overlays inject their own instance with a restricted config.
    """

    def __init__(self, config: TrustAnchorConfig | None = None) -> None:
        if config is not None:
            self._config = config
        else:
            self._config = TrustAnchorConfig.from_file(
                _DEFAULT_TRUST_ANCHOR_FILE,
                expected_sha256=_DEFAULT_TRUST_ANCHOR_SHA256,
            )

    # ------------------------------------------------------------------
    # TrustAnchorOverlayProvider interface
    # ------------------------------------------------------------------

    def overlay_anchors(
        self,
        base_anchors: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Filter ``base_anchors`` to those present in the local config.

        If the local config has no anchors (default), all base anchors pass
        through unchanged — this represents the open Gaia-X baseline posture.

        If the config has anchors, only base_anchors whose ``did`` appears in
        the config (and is active) are returned.

        Args:
            base_anchors: List of anchor dicts from the trust store.

        Returns:
            Filtered (or unchanged) list of anchor dicts.
        """
        if not self._config.anchors:
            # No local restriction — pass everything through
            return list(base_anchors)

        allowed_dids: set[str] = {
            a.did for a in self._config.active_anchors()
        }
        return [a for a in base_anchors if a.get("did") in allowed_dids]
