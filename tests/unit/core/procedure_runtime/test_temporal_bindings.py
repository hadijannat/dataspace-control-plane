"""
tests/unit/core/procedure_runtime/test_temporal_bindings.py
Unit tests for procedure_runtime/temporal_bindings/ — converters, decorators, interceptors.

Covers:
  - converters.encode_search_attributes() — returns shallow copy, handles empty dict
  - decorators.procedure_binding() — pass-through marker, does not mutate the function
  - interceptors.ProcedureInterceptor — stores name, frozen

All tests are pure logic — no Temporal SDK dependency, no network.
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
    from dataspace_control_plane_core.procedure_runtime.temporal_bindings.converters import (
        encode_search_attributes,
    )
    from dataspace_control_plane_core.procedure_runtime.temporal_bindings.decorators import (
        procedure_binding,
    )
    from dataspace_control_plane_core.procedure_runtime.temporal_bindings.interceptors import (
        ProcedureInterceptor,
    )
    _AVAILABLE = True
except ImportError as _e:
    _AVAILABLE = False
    _IMPORT_ERROR = str(_e)


def _skip_if_missing() -> None:
    if not _AVAILABLE:
        pytest.skip(f"temporal_bindings not available: {_IMPORT_ERROR}")


# ── encode_search_attributes ──────────────────────────────────────────────────


def test_encode_search_attributes_returns_dict() -> None:
    """encode_search_attributes() must return a dict."""
    _skip_if_missing()
    result = encode_search_attributes({"tenant_id": "t1", "status": "running"})
    assert isinstance(result, dict)


def test_encode_search_attributes_round_trips_values() -> None:
    """encode_search_attributes() must preserve all key-value pairs."""
    _skip_if_missing()
    attrs = {"tenant_id": "t1", "procedure_type": "company-onboarding", "status": "running"}
    result = encode_search_attributes(attrs)
    assert result == attrs


def test_encode_search_attributes_returns_shallow_copy() -> None:
    """encode_search_attributes() must return a distinct dict object (not the same reference)."""
    _skip_if_missing()
    attrs = {"tenant_id": "t1"}
    result = encode_search_attributes(attrs)
    assert result is not attrs


def test_encode_search_attributes_with_empty_dict() -> None:
    """encode_search_attributes() must handle an empty input dict."""
    _skip_if_missing()
    result = encode_search_attributes({})
    assert result == {}


def test_encode_search_attributes_does_not_mutate_input() -> None:
    """encode_search_attributes() must not mutate the input dict."""
    _skip_if_missing()
    original = {"tenant_id": "t1"}
    _ = encode_search_attributes(original)
    assert original == {"tenant_id": "t1"}


# ── procedure_binding decorator ───────────────────────────────────────────────


def test_procedure_binding_returns_same_function() -> None:
    """procedure_binding() must return the exact same callable it receives."""
    _skip_if_missing()

    def my_workflow() -> str:
        return "executed"

    decorated = procedure_binding(my_workflow)
    assert decorated is my_workflow


def test_procedure_binding_decorated_function_still_callable() -> None:
    """A function decorated with procedure_binding() must remain callable."""
    _skip_if_missing()

    @procedure_binding
    def my_fn(x: int) -> int:
        return x * 2

    assert my_fn(5) == 10


def test_procedure_binding_preserves_function_name() -> None:
    """procedure_binding() must not alter __name__ of the decorated function."""
    _skip_if_missing()

    def my_activity() -> None:
        pass

    decorated = procedure_binding(my_activity)
    assert decorated.__name__ == "my_activity"


# ── ProcedureInterceptor ──────────────────────────────────────────────────────


def test_procedure_interceptor_stores_name() -> None:
    """ProcedureInterceptor must store the provided name."""
    _skip_if_missing()
    pi = ProcedureInterceptor(name="audit-interceptor")
    assert pi.name == "audit-interceptor"


def test_procedure_interceptor_is_frozen() -> None:
    """ProcedureInterceptor is a frozen dataclass — mutation must raise."""
    _skip_if_missing()
    pi = ProcedureInterceptor(name="test-interceptor")
    with pytest.raises((AttributeError, TypeError)):
        pi.name = "tampered"  # type: ignore[misc]


def test_procedure_interceptor_equality() -> None:
    """Two ProcedureInterceptors with the same name must be equal."""
    _skip_if_missing()
    a = ProcedureInterceptor(name="shared-interceptor")
    b = ProcedureInterceptor(name="shared-interceptor")
    assert a == b


def test_procedure_interceptor_inequality() -> None:
    """Two ProcedureInterceptors with different names must not be equal."""
    _skip_if_missing()
    a = ProcedureInterceptor(name="audit")
    b = ProcedureInterceptor(name="metrics")
    assert a != b
