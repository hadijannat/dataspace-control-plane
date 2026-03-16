"""
tests/unit/test_marker_enforcement.py

Unit tests for the autouse marker enforcement fixture in tests/conftest.py.
Guards against accidental narrowing of _GUARDED_MARKS that would let live-service
tests run silently in CI without --live-services.
"""
from __future__ import annotations

import pytest


def test_guarded_marks_contains_all_live_service_markers() -> None:
    """
    _GUARDED_MARKS must contain every marker that gates live-service tests.

    If this test fails, a marker was removed from _GUARDED_MARKS. That means
    tests carrying that marker would run without --live-services in CI and
    silently pass against unprovisioned infrastructure.
    """
    from tests.conftest import _GUARDED_MARKS

    required = {"integration", "chaos", "tenancy", "crypto", "e2e", "compatibility"}
    missing = required - _GUARDED_MARKS
    assert not missing, (
        f"_GUARDED_MARKS is missing required marks: {missing}. "
        "Tests carrying these marks would run without --live-services."
    )
