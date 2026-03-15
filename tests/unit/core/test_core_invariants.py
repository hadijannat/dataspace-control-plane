"""
tests/unit/core/test_core_invariants.py
Unit tests for core/ domain invariant behavior.

Covers:
  - AggregateRoot event accumulation and drain (pull_events is idempotent reset)
  - AuditRecord.new() produces a valid, frozen record with all required fields
  - AuditRecord.new() is frozen — mutation raises FrozenInstanceError
  - ProcedureType → task_queue mapping covers all enum members (no unmapped type)
  - task_queue_for() raises ValueError for an unknown type
  - validate_procedure_input() passes when all required payload keys are present
  - validate_procedure_input() raises ProcedureInputValidationError for missing keys
  - TenantId raises ValueError for blank string
  - LegalEntityId raises ValueError for blank string
  - CorrelationContext.new() produces unique correlation IDs

All tests are pure logic — no network, no containers, no wall-clock side-effects.
Marker: unit
"""
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

import pytest

pytestmark = pytest.mark.unit

# ── Path injection so tests run even when core isn't pip-installed ─────────────
_CORE_SRC = Path(__file__).resolve().parent.parent.parent.parent / "core" / "src"
if _CORE_SRC.exists() and str(_CORE_SRC) not in sys.path:
    sys.path.insert(0, str(_CORE_SRC))


# Graceful skip if the core package is absent from the environment.
try:
    from dataspace_control_plane_core.domains._shared.aggregate import AggregateRoot
    from dataspace_control_plane_core.domains._shared.events import DomainEvent
    from dataspace_control_plane_core.domains._shared.ids import (
        AggregateId,
        LegalEntityId,
        TenantId,
        WorkflowId,
    )
    from dataspace_control_plane_core.domains._shared.actor import ActorRef, ActorType
    from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
    from dataspace_control_plane_core.audit.record import (
        AuditCategory,
        AuditOutcome,
        AuditRecord,
    )
    from dataspace_control_plane_core.procedure_runtime.contracts import (
        ProcedureInput,
        ProcedureType,
    )
    from dataspace_control_plane_core.procedure_runtime.task_queues import (
        TASK_QUEUE_MAP,
        task_queue_for,
    )
    from dataspace_control_plane_core.procedure_runtime.validation import (
        validate_procedure_input,
    )
    from dataspace_control_plane_core.procedure_runtime.errors import (
        ProcedureInputValidationError,
    )

    _CORE_AVAILABLE = True
except ImportError as _e:
    _CORE_AVAILABLE = False
    _IMPORT_ERROR = str(_e)


def _skip_if_missing() -> None:
    if not _CORE_AVAILABLE:
        pytest.skip(f"core package not available: {_IMPORT_ERROR}")


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_tenant() -> "TenantId":
    return TenantId("tenant-test-001")


def _make_actor() -> "ActorRef":
    return ActorRef(subject="test-service", actor_type=ActorType.SERVICE)


def _make_correlation() -> "CorrelationContext":
    return CorrelationContext.new()


def _make_procedure_input(
    procedure_type: "ProcedureType", payload: dict
) -> "ProcedureInput":
    from dataspace_control_plane_core.domains._shared.actor import ActorRef, ActorType
    return ProcedureInput(
        tenant_id=_make_tenant(),
        procedure_type=procedure_type,
        payload=payload,
        actor=_make_actor(),
        correlation=_make_correlation(),
    )


# ── AggregateRoot ─────────────────────────────────────────────────────────────


def test_aggregate_root_accumulates_events() -> None:
    """_raise_event() accumulates domain events on the aggregate."""
    _skip_if_missing()

    agg = AggregateRoot(
        id=AggregateId.generate(),
        tenant_id=_make_tenant(),
    )
    # Before any events: empty
    assert agg._pending_events == []

    event_a = DomainEvent()
    event_b = DomainEvent()
    agg._raise_event(event_a)
    agg._raise_event(event_b)

    assert len(agg._pending_events) == 2


def test_aggregate_root_pull_events_drains_and_returns() -> None:
    """pull_events() returns all pending events and clears the internal list."""
    _skip_if_missing()

    agg = AggregateRoot(
        id=AggregateId.generate(),
        tenant_id=_make_tenant(),
    )
    ev1 = DomainEvent()
    ev2 = DomainEvent()
    agg._raise_event(ev1)
    agg._raise_event(ev2)

    drained = agg.pull_events()

    assert ev1 in drained
    assert ev2 in drained
    assert len(drained) == 2
    # After drain: internal list is empty
    assert agg._pending_events == []


def test_aggregate_root_pull_events_is_idempotent() -> None:
    """Second pull_events() on an already-drained aggregate returns an empty list."""
    _skip_if_missing()

    agg = AggregateRoot(
        id=AggregateId.generate(),
        tenant_id=_make_tenant(),
    )
    agg._raise_event(DomainEvent())
    agg.pull_events()          # first drain
    second = agg.pull_events() # second call — must be empty
    assert second == []


# ── AuditRecord ───────────────────────────────────────────────────────────────


def test_audit_record_new_creates_valid_record() -> None:
    """AuditRecord.new() must produce a record with all required fields populated."""
    _skip_if_missing()

    record = AuditRecord.new(
        tenant_id=_make_tenant(),
        category=AuditCategory.TENANCY,
        action="tenant_topology.activate",
        outcome=AuditOutcome.SUCCESS,
        actor=_make_actor(),
        correlation=_make_correlation(),
    )

    assert record.record_id, "record_id must be non-empty"
    assert record.tenant_id == _make_tenant()
    assert record.category == AuditCategory.TENANCY
    assert record.action == "tenant_topology.activate"
    assert record.outcome == AuditOutcome.SUCCESS
    assert record.occurred_at is not None


def test_audit_record_new_is_frozen() -> None:
    """AuditRecord is a frozen dataclass — mutation must raise an error."""
    _skip_if_missing()

    record = AuditRecord.new(
        tenant_id=_make_tenant(),
        category=AuditCategory.SECURITY,
        action="auth.failed",
        outcome=AuditOutcome.DENIED,
        actor=_make_actor(),
        correlation=_make_correlation(),
    )

    with pytest.raises((AttributeError, TypeError)):
        record.action = "tampered"  # type: ignore[misc]


def test_audit_record_new_produces_unique_ids() -> None:
    """Two consecutive AuditRecord.new() calls must produce distinct record_ids."""
    _skip_if_missing()

    r1 = AuditRecord.new(
        tenant_id=_make_tenant(),
        category=AuditCategory.ADMIN,
        action="config.changed",
        outcome=AuditOutcome.SUCCESS,
        actor=_make_actor(),
        correlation=_make_correlation(),
    )
    r2 = AuditRecord.new(
        tenant_id=_make_tenant(),
        category=AuditCategory.ADMIN,
        action="config.changed",
        outcome=AuditOutcome.SUCCESS,
        actor=_make_actor(),
        correlation=_make_correlation(),
    )
    assert r1.record_id != r2.record_id


# ── ProcedureType → task queue ────────────────────────────────────────────────


def test_task_queue_map_covers_all_procedure_types() -> None:
    """Every ProcedureType enum member must appear in TASK_QUEUE_MAP."""
    _skip_if_missing()

    all_types = set(ProcedureType)
    mapped_types = set(TASK_QUEUE_MAP.keys())
    unmapped = all_types - mapped_types
    assert not unmapped, (
        f"ProcedureType members missing from TASK_QUEUE_MAP: {unmapped}\n"
        "Add each new procedure type to core/procedure_runtime/task_queues.py"
    )


@pytest.mark.parametrize(
    "procedure_type, expected_queue",
    [
        (ProcedureType.COMPANY_ONBOARDING, "onboarding"),
        (ProcedureType.CONNECTOR_BOOTSTRAP, "onboarding"),
        (ProcedureType.MACHINE_CREDENTIAL_ROTATION, "machine-trust"),
        (ProcedureType.ASSET_TWIN_PUBLICATION, "twins-publication"),
        (ProcedureType.CONTRACT_NEGOTIATION, "contracts-negotiation"),
        (ProcedureType.COMPLIANCE_GAP_SCAN, "compliance"),
        (ProcedureType.STALE_NEGOTIATION_SWEEP, "maintenance"),
    ]
    if _CORE_AVAILABLE
    else [],
)
def test_task_queue_for_known_types(
    procedure_type: "ProcedureType", expected_queue: str
) -> None:
    """task_queue_for() must return the expected queue name for each procedure type."""
    _skip_if_missing()
    assert task_queue_for(procedure_type) == expected_queue


# ── validate_procedure_input ──────────────────────────────────────────────────


def test_validate_procedure_input_passes_with_all_required_keys() -> None:
    """validate_procedure_input() must not raise when all required keys are present."""
    _skip_if_missing()

    inp = _make_procedure_input(
        ProcedureType.COMPANY_ONBOARDING,
        payload={"legal_entity_id": "BPN000", "bpnl": "BPNL000000000001"},
    )
    # Must not raise
    validate_procedure_input(inp)


def test_validate_procedure_input_raises_for_missing_keys() -> None:
    """validate_procedure_input() must raise ProcedureInputValidationError on missing keys."""
    _skip_if_missing()

    inp = _make_procedure_input(
        ProcedureType.COMPANY_ONBOARDING,
        payload={},  # missing legal_entity_id and bpnl
    )
    with pytest.raises(ProcedureInputValidationError):
        validate_procedure_input(inp)


def test_validate_procedure_input_reports_exact_missing_keys() -> None:
    """The error message must name the specific missing payload keys."""
    _skip_if_missing()

    inp = _make_procedure_input(
        ProcedureType.CONTRACT_NEGOTIATION,
        payload={"legal_entity_id": "BPN000"},  # offer_id and counterparty_connector missing
    )
    with pytest.raises(ProcedureInputValidationError) as exc_info:
        validate_procedure_input(inp)

    error_msg = str(exc_info.value)
    assert "offer_id" in error_msg or "counterparty_connector" in error_msg, (
        f"Error message must name missing keys; got: {error_msg!r}"
    )


def test_validate_procedure_input_passes_for_no_required_keys() -> None:
    """A procedure type with no required keys must always pass validation."""
    _skip_if_missing()

    inp = _make_procedure_input(
        ProcedureType.STALE_NEGOTIATION_SWEEP,
        payload={},  # no required keys for this procedure
    )
    validate_procedure_input(inp)


# ── Typed ID value objects ─────────────────────────────────────────────────────


def test_tenant_id_rejects_blank_string() -> None:
    """TenantId must raise ValueError for blank or empty strings."""
    _skip_if_missing()

    with pytest.raises(ValueError):
        TenantId("")

    with pytest.raises(ValueError):
        TenantId("   ")


def test_legal_entity_id_rejects_blank_string() -> None:
    """LegalEntityId must raise ValueError for blank or empty strings."""
    _skip_if_missing()

    with pytest.raises(ValueError):
        LegalEntityId("")


def test_tenant_id_str_representation() -> None:
    """str(TenantId) must return the raw value string."""
    _skip_if_missing()

    tid = TenantId("my-tenant")
    assert str(tid) == "my-tenant"


def test_aggregate_id_generate_produces_unique_ids() -> None:
    """AggregateId.generate() must produce distinct IDs on successive calls."""
    _skip_if_missing()

    a = AggregateId.generate()
    b = AggregateId.generate()
    assert a != b
    assert isinstance(a.value, UUID)


# ── CorrelationContext ────────────────────────────────────────────────────────


def test_correlation_context_new_produces_unique_ids() -> None:
    """CorrelationContext.new() must produce distinct correlation_ids."""
    _skip_if_missing()

    c1 = CorrelationContext.new()
    c2 = CorrelationContext.new()
    assert c1.correlation_id != c2.correlation_id


def test_correlation_context_caused_by_preserves_correlation_id() -> None:
    """caused_by() must preserve the parent correlation_id."""
    _skip_if_missing()
    from uuid import uuid4

    parent = CorrelationContext.new()
    cause_id = uuid4()
    child = parent.caused_by(cause_id)

    assert child.correlation_id == parent.correlation_id
    assert child.causation_id == cause_id
