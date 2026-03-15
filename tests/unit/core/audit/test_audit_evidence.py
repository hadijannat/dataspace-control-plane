"""
tests/unit/core/audit/test_audit_evidence.py
Unit tests for audit evidence value objects:
  - signing.SignatureRef
  - lineage.LineageLink
  - redaction.RedactionDecision
  - retention.RetentionPolicy
  - manifests.EvidenceManifestEntry, EvidenceManifest
  - exports.EvidenceExport

Tests:
  1. SignatureRef stores all fields and is frozen
  2. LineageLink stores source_id, target_id, relation and is frozen
  3. RedactionDecision stores redaction_class with optional rationale
  4. RetentionPolicy stores retention_class, purge_after_days, legal_hold_required
  5. EvidenceManifestEntry stores item_id, digest, media_type, storage_uri and is frozen
  6. EvidenceManifest stores manifest_id, tenant_id, subject and is frozen
  7. EvidenceManifest with entries tuple
  8. EvidenceManifest with lineage links
  9. EvidenceExport stores export_id, manifest, format, destination_uri and is frozen
  10. EvidenceExport with optional digest and signature

All tests are pure logic — no network, no containers.
Marker: unit
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_CORE_SRC = Path(__file__).resolve().parent.parent.parent.parent.parent / "core" / "src"
if _CORE_SRC.exists() and str(_CORE_SRC) not in sys.path:
    # Append rather than insert so that PYTHONPATH-provided paths take precedence.
    sys.path.append(str(_CORE_SRC))

try:
    from dataspace_control_plane_core.audit.signing import SignatureRef
    from dataspace_control_plane_core.audit.lineage import LineageLink
    from dataspace_control_plane_core.audit.redaction import RedactionDecision
    from dataspace_control_plane_core.audit.retention import RetentionPolicy
    from dataspace_control_plane_core.audit.manifests import (
        EvidenceManifest,
        EvidenceManifestEntry,
    )
    from dataspace_control_plane_core.audit.exports import EvidenceExport
    from dataspace_control_plane_core.audit.hashing import HashDigest, digest_bytes
    from dataspace_control_plane_core.canonical_models.enums import RetentionClass, RedactionClass
    from dataspace_control_plane_core.domains._shared.ids import TenantId
    _AVAILABLE = True
except ImportError as _e:
    _AVAILABLE = False
    _IMPORT_ERROR = str(_e)


def _skip_if_missing() -> None:
    if not _AVAILABLE:
        pytest.skip(f"audit evidence modules not available: {_IMPORT_ERROR}")


_FIXED_DATETIME = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)


# ── SignatureRef ──────────────────────────────────────────────────────────────


def test_signature_ref_stores_all_fields() -> None:
    """SignatureRef must store signature_id, signer_key_ref, and algorithm."""
    _skip_if_missing()
    sr = SignatureRef(
        signature_id="sig-001",
        signer_key_ref="vault/transit/key-001",
        algorithm="EdDSA",
        signed_at=_FIXED_DATETIME,
    )
    assert sr.signature_id == "sig-001"
    assert sr.signer_key_ref == "vault/transit/key-001"
    assert sr.algorithm == "EdDSA"
    assert sr.signed_at == _FIXED_DATETIME


def test_signature_ref_is_frozen() -> None:
    """SignatureRef is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    sr = SignatureRef(
        signature_id="sig-001",
        signer_key_ref="key-ref",
        algorithm="ES256",
        signed_at=_FIXED_DATETIME,
    )
    with pytest.raises((AttributeError, TypeError)):
        sr.algorithm = "tampered"  # type: ignore[misc]


# ── LineageLink ───────────────────────────────────────────────────────────────


def test_lineage_link_stores_fields() -> None:
    """LineageLink must store source_id, target_id, and relation."""
    _skip_if_missing()
    ll = LineageLink(source_id="record-aaa", target_id="export-bbb", relation="derives_from")
    assert ll.source_id == "record-aaa"
    assert ll.target_id == "export-bbb"
    assert ll.relation == "derives_from"


def test_lineage_link_is_frozen() -> None:
    """LineageLink is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    ll = LineageLink(source_id="src", target_id="tgt", relation="derived")
    with pytest.raises((AttributeError, TypeError)):
        ll.relation = "tampered"  # type: ignore[misc]


def test_lineage_links_equality() -> None:
    """Two LineageLinks with identical fields must be equal."""
    _skip_if_missing()
    l1 = LineageLink(source_id="a", target_id="b", relation="r")
    l2 = LineageLink(source_id="a", target_id="b", relation="r")
    assert l1 == l2


# ── RedactionDecision ─────────────────────────────────────────────────────────


def test_redaction_decision_stores_class_and_rationale() -> None:
    """RedactionDecision must store redaction_class and optional rationale."""
    _skip_if_missing()
    rd = RedactionDecision(redaction_class=RedactionClass.PARTIAL, rationale="PII fields masked")
    assert rd.redaction_class == RedactionClass.PARTIAL
    assert rd.rationale == "PII fields masked"


def test_redaction_decision_default_rationale_is_empty() -> None:
    """RedactionDecision defaults to empty rationale string."""
    _skip_if_missing()
    rd = RedactionDecision(redaction_class=RedactionClass.NONE)
    assert rd.rationale == ""


def test_redaction_decision_is_frozen() -> None:
    """RedactionDecision is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    rd = RedactionDecision(redaction_class=RedactionClass.FULL)
    with pytest.raises((AttributeError, TypeError)):
        rd.rationale = "tampered"  # type: ignore[misc]


# ── RetentionPolicy ───────────────────────────────────────────────────────────


def test_retention_policy_stores_all_fields() -> None:
    """RetentionPolicy must store retention_class, purge_after_days, and legal_hold_required."""
    _skip_if_missing()
    rp = RetentionPolicy(
        retention_class=RetentionClass.TEN_YEARS,
        purge_after_days=3650,
        legal_hold_required=True,
    )
    assert rp.retention_class == RetentionClass.TEN_YEARS
    assert rp.purge_after_days == 3650
    assert rp.legal_hold_required is True


def test_retention_policy_defaults() -> None:
    """RetentionPolicy defaults: purge_after_days=None, legal_hold_required=False."""
    _skip_if_missing()
    rp = RetentionPolicy(retention_class=RetentionClass.SEVEN_YEARS)
    assert rp.purge_after_days is None
    assert rp.legal_hold_required is False


def test_retention_policy_is_frozen() -> None:
    """RetentionPolicy is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    rp = RetentionPolicy(retention_class=RetentionClass.INDEFINITE)
    with pytest.raises((AttributeError, TypeError)):
        rp.legal_hold_required = True  # type: ignore[misc]


# ── EvidenceManifestEntry ─────────────────────────────────────────────────────


def test_evidence_manifest_entry_stores_fields() -> None:
    """EvidenceManifestEntry must store item_id, digest, media_type, and storage_uri."""
    _skip_if_missing()
    digest = HashDigest(algorithm="sha256", hex_value="abcdef01")
    entry = EvidenceManifestEntry(
        item_id="item-001",
        digest=digest,
        media_type="application/json",
        storage_uri="s3://bucket/evidence/item-001",
    )
    assert entry.item_id == "item-001"
    assert entry.digest == digest
    assert entry.media_type == "application/json"
    assert entry.storage_uri == "s3://bucket/evidence/item-001"


def test_evidence_manifest_entry_is_frozen() -> None:
    """EvidenceManifestEntry is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    digest = HashDigest(algorithm="sha256", hex_value="abcdef01")
    entry = EvidenceManifestEntry(
        item_id="item-001",
        digest=digest,
        media_type="application/json",
        storage_uri="s3://bucket/item",
    )
    with pytest.raises((AttributeError, TypeError)):
        entry.item_id = "tampered"  # type: ignore[misc]


# ── EvidenceManifest ──────────────────────────────────────────────────────────


def test_evidence_manifest_stores_required_fields() -> None:
    """EvidenceManifest must store manifest_id, tenant_id, subject_id, subject_type."""
    _skip_if_missing()
    tenant = TenantId("test-tenant")
    m = EvidenceManifest(
        manifest_id="manifest-001",
        tenant_id=tenant,
        subject_id="assessment-aaa",
        subject_type="compliance_assessment",
    )
    assert m.manifest_id == "manifest-001"
    assert m.tenant_id == tenant
    assert m.subject_id == "assessment-aaa"
    assert m.subject_type == "compliance_assessment"


def test_evidence_manifest_default_entries_and_lineage_are_empty() -> None:
    """EvidenceManifest defaults to empty entries and lineage tuples."""
    _skip_if_missing()
    m = EvidenceManifest(
        manifest_id="m-001",
        tenant_id=TenantId("t1"),
        subject_id="sub",
        subject_type="onboarding",
    )
    assert m.entries == ()
    assert m.lineage == ()
    assert m.signature is None


def test_evidence_manifest_with_entries() -> None:
    """EvidenceManifest must hold the provided entries tuple."""
    _skip_if_missing()
    digest = digest_bytes(b"workflow history payload")
    entry = EvidenceManifestEntry(
        item_id="entry-001",
        digest=digest,
        media_type="application/octet-stream",
        storage_uri="s3://bucket/entry-001",
    )
    m = EvidenceManifest(
        manifest_id="m-with-entries",
        tenant_id=TenantId("t1"),
        subject_id="sub",
        subject_type="agreement",
        entries=(entry,),
    )
    assert len(m.entries) == 1
    assert m.entries[0] == entry


def test_evidence_manifest_with_lineage_links() -> None:
    """EvidenceManifest must hold the provided lineage tuple."""
    _skip_if_missing()
    ll = LineageLink(source_id="src", target_id="tgt", relation="derived_from")
    m = EvidenceManifest(
        manifest_id="m-with-lineage",
        tenant_id=TenantId("t1"),
        subject_id="sub",
        subject_type="compliance",
        lineage=(ll,),
    )
    assert len(m.lineage) == 1
    assert m.lineage[0] == ll


def test_evidence_manifest_is_frozen() -> None:
    """EvidenceManifest is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    m = EvidenceManifest(
        manifest_id="m-frozen",
        tenant_id=TenantId("t1"),
        subject_id="sub",
        subject_type="trust",
    )
    with pytest.raises((AttributeError, TypeError)):
        m.manifest_id = "tampered"  # type: ignore[misc]


# ── EvidenceExport ────────────────────────────────────────────────────────────


def _make_manifest() -> "EvidenceManifest":
    return EvidenceManifest(
        manifest_id="manifest-export-001",
        tenant_id=TenantId("export-tenant"),
        subject_id="subject-001",
        subject_type="data_exchange",
    )


def test_evidence_export_stores_required_fields() -> None:
    """EvidenceExport must store export_id, manifest, format, and destination_uri."""
    _skip_if_missing()
    m = _make_manifest()
    export = EvidenceExport(
        export_id="export-001",
        manifest=m,
        format="json",
        destination_uri="s3://bucket/exports/export-001.json",
    )
    assert export.export_id == "export-001"
    assert export.manifest is m
    assert export.format == "json"
    assert export.destination_uri == "s3://bucket/exports/export-001.json"


def test_evidence_export_optional_fields_default_to_none() -> None:
    """EvidenceExport digest and signature default to None."""
    _skip_if_missing()
    export = EvidenceExport(
        export_id="export-002",
        manifest=_make_manifest(),
        format="cbor",
        destination_uri="s3://bucket/exports/e2.cbor",
    )
    assert export.digest is None
    assert export.signature is None


def test_evidence_export_with_digest() -> None:
    """EvidenceExport stores the provided HashDigest."""
    _skip_if_missing()
    digest = digest_bytes(b"exported bundle bytes")
    export = EvidenceExport(
        export_id="export-003",
        manifest=_make_manifest(),
        format="json",
        destination_uri="s3://bucket/exports/e3.json",
        digest=digest,
    )
    assert export.digest == digest


def test_evidence_export_with_signature() -> None:
    """EvidenceExport stores the provided SignatureRef."""
    _skip_if_missing()
    sig = SignatureRef(
        signature_id="sig-export-001",
        signer_key_ref="vault/key/export-signer",
        algorithm="EdDSA",
        signed_at=_FIXED_DATETIME,
    )
    export = EvidenceExport(
        export_id="export-004",
        manifest=_make_manifest(),
        format="json",
        destination_uri="s3://bucket/exports/e4.json",
        signature=sig,
    )
    assert export.signature == sig


def test_evidence_export_is_frozen() -> None:
    """EvidenceExport is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    export = EvidenceExport(
        export_id="export-005",
        manifest=_make_manifest(),
        format="json",
        destination_uri="s3://bucket/exports/e5.json",
    )
    with pytest.raises((AttributeError, TypeError)):
        export.export_id = "tampered"  # type: ignore[misc]
