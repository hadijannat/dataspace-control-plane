"""
tests/unit/core/audit/test_records.py
Unit tests for audit/records.py — AuditActor, AuditSubject, and the new AuditRecord.

Tests:
  1. AuditActor.from_actor_ref() maps ActorRef fields correctly
  2. AuditActor is frozen — mutation raises
  3. AuditSubject holds subject_id and subject_type correctly
  4. AuditSubject is frozen — mutation raises
  5. AuditRecord.new() populates all required fields
  6. AuditRecord.new() is frozen — mutation raises
  7. AuditRecord.new() produces unique record_ids on successive calls
  8. AuditRecord.new() convenience properties delegate to nested subject/correlation
  9. AuditRecord.new() with pack_ids tuple is stored correctly
  10. AuditRecord.new() with legal_entity_id stores it correctly
  11. default_id_factory() injectable — use_id_factory() overrides record_id generation

All tests are pure logic — no network, no containers.
Marker: unit
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_CORE_SRC = Path(__file__).resolve().parent.parent.parent.parent.parent / "core" / "src"
if _CORE_SRC.exists() and str(_CORE_SRC) not in sys.path:
    # Append rather than insert so that PYTHONPATH-provided paths take precedence.
    sys.path.append(str(_CORE_SRC))

try:
    from dataspace_control_plane_core.audit.records import (
        AuditActor,
        AuditCategory,
        AuditOutcome,
        AuditRecord,
        AuditSubject,
    )
    from dataspace_control_plane_core.domains._shared.actor import ActorRef, ActorType
    from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
    from dataspace_control_plane_core.domains._shared.ids import (
        LegalEntityId,
        TenantId,
        use_id_factory,
    )
    from dataspace_control_plane_core.canonical_models.enums import RetentionClass, RedactionClass
    _AVAILABLE = True
except ImportError as _e:
    _AVAILABLE = False
    _IMPORT_ERROR = str(_e)


def _skip_if_missing() -> None:
    if not _AVAILABLE:
        pytest.skip(f"audit.records not available: {_IMPORT_ERROR}")


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _actor() -> "ActorRef":
    return ActorRef(subject="svc-test", actor_type=ActorType.SERVICE, display_name="Test Service")


def _human_actor() -> "ActorRef":
    return ActorRef(subject="user@example.com", actor_type=ActorType.HUMAN, display_name="Test User")


def _tenant() -> "TenantId":
    return TenantId("test-tenant-001")


def _correlation() -> "CorrelationContext":
    return CorrelationContext.new()


def _record(**kwargs) -> "AuditRecord":
    defaults = dict(
        tenant_id=_tenant(),
        category=AuditCategory.TENANCY,
        action="test.action",
        outcome=AuditOutcome.SUCCESS,
        actor=_actor(),
        correlation=_correlation(),
    )
    defaults.update(kwargs)
    return AuditRecord.new(**defaults)


# ── AuditActor ────────────────────────────────────────────────────────────────


def test_audit_actor_from_actor_ref_copies_fields() -> None:
    """AuditActor.from_actor_ref() must copy subject, actor_type value, and display_name."""
    _skip_if_missing()
    ref = _actor()
    aa = AuditActor.from_actor_ref(ref)
    assert aa.subject == ref.subject
    assert aa.actor_type == ref.actor_type.value
    assert aa.display_name == ref.display_name


def test_audit_actor_from_human_actor_ref() -> None:
    """AuditActor.from_actor_ref() must work for human actors."""
    _skip_if_missing()
    ref = _human_actor()
    aa = AuditActor.from_actor_ref(ref)
    assert aa.subject == "user@example.com"
    assert aa.actor_type == "human"


def test_audit_actor_is_frozen() -> None:
    """AuditActor is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    aa = AuditActor(subject="svc", actor_type="service")
    with pytest.raises((AttributeError, TypeError)):
        aa.subject = "tampered"  # type: ignore[misc]


# ── AuditSubject ──────────────────────────────────────────────────────────────


def test_audit_subject_holds_id_and_type() -> None:
    """AuditSubject must store subject_id and subject_type as given."""
    _skip_if_missing()
    s = AuditSubject(subject_id="agg-123", subject_type="tenant_topology")
    assert s.subject_id == "agg-123"
    assert s.subject_type == "tenant_topology"


def test_audit_subject_is_frozen() -> None:
    """AuditSubject is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    s = AuditSubject(subject_id="agg-123", subject_type="compliance")
    with pytest.raises((AttributeError, TypeError)):
        s.subject_id = "tampered"  # type: ignore[misc]


# ── AuditRecord.new() ─────────────────────────────────────────────────────────


def test_audit_record_new_populates_required_fields() -> None:
    """AuditRecord.new() must populate all required structural fields."""
    _skip_if_missing()
    r = _record()
    assert r.record_id, "record_id must be non-empty"
    assert r.tenant_id == _tenant()
    assert r.category == AuditCategory.TENANCY
    assert r.action == "test.action"
    assert r.outcome == AuditOutcome.SUCCESS
    assert r.occurred_at is not None


def test_audit_record_new_is_frozen() -> None:
    """AuditRecord is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    r = _record()
    with pytest.raises((AttributeError, TypeError)):
        r.action = "tampered"  # type: ignore[misc]


def test_audit_record_new_produces_unique_ids() -> None:
    """Two consecutive AuditRecord.new() calls must produce distinct record_ids."""
    _skip_if_missing()
    r1 = _record()
    r2 = _record()
    assert r1.record_id != r2.record_id


def test_audit_record_subject_properties_delegate_to_nested() -> None:
    """AuditRecord.subject_id and subject_type must delegate to the nested AuditSubject."""
    _skip_if_missing()
    r = _record(subject_id="agg-456", subject_type="contract")
    assert r.subject_id == "agg-456"
    assert r.subject_type == "contract"


def test_audit_record_correlation_properties_delegate_to_correlation() -> None:
    """AuditRecord.correlation_id must delegate to the embedded CorrelationContext."""
    _skip_if_missing()
    corr = _correlation()
    r = AuditRecord.new(
        tenant_id=_tenant(),
        category=AuditCategory.CONTRACT,
        action="contract.agreed",
        outcome=AuditOutcome.SUCCESS,
        actor=_actor(),
        correlation=corr,
    )
    assert r.correlation_id == corr.correlation_id


def test_audit_record_new_with_pack_ids_tuple() -> None:
    """AuditRecord.new() must store the provided pack_ids tuple."""
    _skip_if_missing()
    r = _record(pack_ids=("catena-x", "gaia-x"))
    assert r.pack_ids == ("catena-x", "gaia-x")


def test_audit_record_new_with_legal_entity_id() -> None:
    """AuditRecord.new() must store the provided legal_entity_id."""
    _skip_if_missing()
    lei = LegalEntityId("BPNL000000000001")
    r = _record(legal_entity_id=lei)
    assert r.legal_entity_id == lei


def test_audit_record_new_default_retention_and_redaction_classes() -> None:
    """AuditRecord defaults to SEVEN_YEARS retention and NONE redaction."""
    _skip_if_missing()
    r = _record()
    assert r.retention_class == RetentionClass.SEVEN_YEARS
    assert r.redaction_class == RedactionClass.NONE


def test_audit_record_new_with_custom_retention_class() -> None:
    """AuditRecord.new() must honor a custom retention_class."""
    _skip_if_missing()
    r = _record(retention_class=RetentionClass.TEN_YEARS)
    assert r.retention_class == RetentionClass.TEN_YEARS


# ── Injectable ID factory ─────────────────────────────────────────────────────


def test_use_id_factory_overrides_record_id_generation() -> None:
    """use_id_factory() context manager must inject deterministic IDs into AuditRecord.new()."""
    _skip_if_missing()
    from uuid import UUID
    from dataspace_control_plane_core.domains._shared.ids import (
        AggregateId,
        WorkflowId,
        SystemIdFactory,
    )

    # Create a factory that always produces a fixed UUID
    FIXED_UUID = UUID("00000000-0000-0000-0000-000000000001")

    class FixedIdFactory:
        def new_aggregate_id(self) -> AggregateId:
            return AggregateId(FIXED_UUID)

        def new_workflow_id(self) -> WorkflowId:
            return WorkflowId(str(FIXED_UUID))

        def new_event_id(self) -> UUID:
            return FIXED_UUID

        def new_request_id(self) -> str:
            return str(FIXED_UUID)

    with use_id_factory(FixedIdFactory()):
        r = _record()

    assert r.record_id == str(FIXED_UUID)


def test_use_id_factory_restores_default_after_context() -> None:
    """After use_id_factory() context exits, the default factory is restored."""
    _skip_if_missing()
    from uuid import UUID
    from dataspace_control_plane_core.domains._shared.ids import AggregateId, WorkflowId

    FIXED_UUID = UUID("00000000-0000-0000-0000-000000000002")

    class FixedFactory:
        def new_aggregate_id(self) -> AggregateId:
            return AggregateId(FIXED_UUID)
        def new_workflow_id(self) -> WorkflowId:
            return WorkflowId(str(FIXED_UUID))
        def new_event_id(self) -> UUID:
            return FIXED_UUID
        def new_request_id(self) -> str:
            return str(FIXED_UUID)

    with use_id_factory(FixedFactory()):
        pass  # no-op

    # After exit, the default factory should generate non-fixed IDs
    r = _record()
    assert r.record_id != str(FIXED_UUID)
