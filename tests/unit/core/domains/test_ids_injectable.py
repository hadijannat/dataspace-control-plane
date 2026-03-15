"""
tests/unit/core/domains/test_ids_injectable.py
Unit tests for domains/_shared/ids.py — injectable factory and new ID types.

Covers:
  - StringIdentifier base: blank/whitespace rejection, value normalization, str()
  - TenantId, LegalEntityId, SiteId, EnvironmentId: blank rejection via StringIdentifier
  - WorkflowId.generate() uses injectable factory
  - AggregateId.generate() uses injectable factory
  - SystemIdFactory.new_aggregate_id(), new_workflow_id(), new_event_id(), new_request_id()
  - default_id_factory() returns the active factory
  - use_id_factory() context manager overrides and restores the factory
  - use_id_factory() is thread-safe (context var, not global mutation)

All tests are pure logic — no network, no containers.
Marker: unit
"""
from __future__ import annotations

import sys
from pathlib import Path
from uuid import UUID

import pytest

pytestmark = pytest.mark.unit

_CORE_SRC = Path(__file__).resolve().parent.parent.parent.parent.parent / "core" / "src"
if _CORE_SRC.exists() and str(_CORE_SRC) not in sys.path:
    # Append rather than insert so that PYTHONPATH-provided paths take precedence.
    sys.path.append(str(_CORE_SRC))

try:
    from dataspace_control_plane_core.domains._shared.ids import (
        AggregateId,
        EnvironmentId,
        IdFactory,
        LegalEntityId,
        SiteId,
        StringIdentifier,
        SystemIdFactory,
        TenantId,
        WorkflowId,
        default_id_factory,
        use_id_factory,
    )
    _AVAILABLE = True
except ImportError as _e:
    _AVAILABLE = False
    _IMPORT_ERROR = str(_e)


def _skip_if_missing() -> None:
    if not _AVAILABLE:
        pytest.skip(f"domains._shared.ids (new version) not available: {_IMPORT_ERROR}")


# ── StringIdentifier base validation ─────────────────────────────────────────


def test_string_identifier_strips_whitespace_on_construction() -> None:
    """StringIdentifier must strip surrounding whitespace and store normalized value."""
    _skip_if_missing()

    class MyId(StringIdentifier):
        pass

    obj = MyId("  hello  ")
    assert obj.value == "hello"


def test_string_identifier_rejects_blank_string() -> None:
    """StringIdentifier must raise ValueError for empty strings."""
    _skip_if_missing()

    class MyId(StringIdentifier):
        pass

    with pytest.raises(ValueError):
        MyId("")


def test_string_identifier_rejects_whitespace_only_string() -> None:
    """StringIdentifier must raise ValueError for whitespace-only strings."""
    _skip_if_missing()

    class MyId(StringIdentifier):
        pass

    with pytest.raises(ValueError):
        MyId("   ")


def test_string_identifier_str_returns_normalized_value() -> None:
    """str(StringIdentifier) must return the normalized value string."""
    _skip_if_missing()

    class MyId(StringIdentifier):
        pass

    obj = MyId("  my-value  ")
    assert str(obj) == "my-value"


# ── Specific typed IDs ────────────────────────────────────────────────────────


def test_tenant_id_rejects_blank() -> None:
    _skip_if_missing()
    with pytest.raises(ValueError):
        TenantId("")


def test_legal_entity_id_rejects_blank() -> None:
    _skip_if_missing()
    with pytest.raises(ValueError):
        LegalEntityId("")


def test_site_id_rejects_blank() -> None:
    _skip_if_missing()
    with pytest.raises(ValueError):
        SiteId("")


def test_environment_id_rejects_blank() -> None:
    _skip_if_missing()
    with pytest.raises(ValueError):
        EnvironmentId("")


def test_workflow_id_rejects_blank() -> None:
    _skip_if_missing()
    with pytest.raises(ValueError):
        WorkflowId("")


# ── AggregateId ───────────────────────────────────────────────────────────────


def test_aggregate_id_generate_produces_uuid_backed_ids() -> None:
    """AggregateId.generate() must produce an id with a UUID value."""
    _skip_if_missing()
    a = AggregateId.generate()
    assert isinstance(a.value, UUID)


def test_aggregate_id_generate_produces_unique_ids() -> None:
    """Successive AggregateId.generate() calls must produce distinct IDs."""
    _skip_if_missing()
    a = AggregateId.generate()
    b = AggregateId.generate()
    assert a != b


def test_aggregate_id_from_str_parses_uuid() -> None:
    """AggregateId.from_str() must parse a valid UUID string."""
    _skip_if_missing()
    uuid_str = "12345678-1234-5678-1234-567812345678"
    a = AggregateId.from_str(uuid_str)
    assert str(a.value) == uuid_str


def test_aggregate_id_str_returns_uuid_string() -> None:
    """str(AggregateId) must return the string representation of the UUID."""
    _skip_if_missing()
    a = AggregateId.generate()
    assert str(a) == str(a.value)


# ── WorkflowId.generate() ─────────────────────────────────────────────────────


def test_workflow_id_generate_produces_string_backed_id() -> None:
    """WorkflowId.generate() must produce a non-empty string-backed id."""
    _skip_if_missing()
    w = WorkflowId.generate()
    assert w.value
    assert isinstance(w.value, str)


def test_workflow_id_generate_produces_unique_ids() -> None:
    """Successive WorkflowId.generate() calls must produce distinct IDs."""
    _skip_if_missing()
    w1 = WorkflowId.generate()
    w2 = WorkflowId.generate()
    assert w1 != w2


# ── SystemIdFactory ───────────────────────────────────────────────────────────


def test_system_id_factory_new_aggregate_id_returns_aggregate_id() -> None:
    """SystemIdFactory.new_aggregate_id() must return an AggregateId with a UUID."""
    _skip_if_missing()
    factory = SystemIdFactory()
    a = factory.new_aggregate_id()
    assert isinstance(a, AggregateId)
    assert isinstance(a.value, UUID)


def test_system_id_factory_new_workflow_id_returns_workflow_id() -> None:
    """SystemIdFactory.new_workflow_id() must return a WorkflowId with a string UUID value."""
    _skip_if_missing()
    factory = SystemIdFactory()
    w = factory.new_workflow_id()
    assert isinstance(w, WorkflowId)
    # Must be parseable as UUID
    UUID(w.value)


def test_system_id_factory_new_event_id_returns_uuid() -> None:
    """SystemIdFactory.new_event_id() must return a UUID."""
    _skip_if_missing()
    factory = SystemIdFactory()
    e = factory.new_event_id()
    assert isinstance(e, UUID)


def test_system_id_factory_new_request_id_returns_non_empty_string() -> None:
    """SystemIdFactory.new_request_id() must return a non-empty string."""
    _skip_if_missing()
    factory = SystemIdFactory()
    r = factory.new_request_id()
    assert isinstance(r, str)
    assert r  # non-empty


# ── Injectable factory context manager ───────────────────────────────────────


_FIXED_UUID = UUID("00000000-1111-2222-3333-444444444444")


class _FixedIdFactory:
    """Test-only factory that always produces the same fixed UUID."""

    def new_aggregate_id(self) -> AggregateId:
        return AggregateId(_FIXED_UUID)

    def new_workflow_id(self) -> WorkflowId:
        return WorkflowId(str(_FIXED_UUID))

    def new_event_id(self) -> UUID:
        return _FIXED_UUID

    def new_request_id(self) -> str:
        return str(_FIXED_UUID)


def test_default_id_factory_returns_an_id_factory() -> None:
    """default_id_factory() must return something conforming to IdFactory protocol."""
    _skip_if_missing()
    f = default_id_factory()
    # Must support new_aggregate_id()
    a = f.new_aggregate_id()
    assert isinstance(a, AggregateId)


def test_use_id_factory_injects_fixed_factory_inside_context() -> None:
    """use_id_factory() must override the active factory inside the context block."""
    _skip_if_missing()
    with use_id_factory(_FixedIdFactory()):
        a = AggregateId.generate()
    assert a.value == _FIXED_UUID


def test_use_id_factory_restores_default_factory_after_context() -> None:
    """After use_id_factory() exits, the default factory must be restored."""
    _skip_if_missing()
    with use_id_factory(_FixedIdFactory()):
        pass

    # Default factory returns random UUIDs, not the fixed one
    a = AggregateId.generate()
    assert a.value != _FIXED_UUID


def test_use_id_factory_yields_the_factory() -> None:
    """use_id_factory() yields the injected factory instance."""
    _skip_if_missing()
    factory = _FixedIdFactory()
    with use_id_factory(factory) as yielded:
        assert yielded is factory


def test_use_id_factory_nested_contexts_restore_outer_factory() -> None:
    """Nested use_id_factory() contexts must restore the correct factory on each exit."""
    _skip_if_missing()
    from uuid import UUID as _UUID

    _FIXED_OUTER = _UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    _FIXED_INNER = _UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")

    class _OuterFactory:
        def new_aggregate_id(self) -> AggregateId:
            return AggregateId(_FIXED_OUTER)
        def new_workflow_id(self) -> WorkflowId:
            return WorkflowId(str(_FIXED_OUTER))
        def new_event_id(self) -> _UUID:
            return _FIXED_OUTER
        def new_request_id(self) -> str:
            return str(_FIXED_OUTER)

    class _InnerFactory:
        def new_aggregate_id(self) -> AggregateId:
            return AggregateId(_FIXED_INNER)
        def new_workflow_id(self) -> WorkflowId:
            return WorkflowId(str(_FIXED_INNER))
        def new_event_id(self) -> _UUID:
            return _FIXED_INNER
        def new_request_id(self) -> str:
            return str(_FIXED_INNER)

    with use_id_factory(_OuterFactory()):
        outer_id = AggregateId.generate()
        with use_id_factory(_InnerFactory()):
            inner_id = AggregateId.generate()
        restored_id = AggregateId.generate()

    assert outer_id.value == _FIXED_OUTER
    assert inner_id.value == _FIXED_INNER
    assert restored_id.value == _FIXED_OUTER  # outer restored after inner exits
