from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_CORE_SRC = Path(__file__).resolve().parents[4] / "core" / "src"
if _CORE_SRC.exists() and str(_CORE_SRC) not in sys.path:
    sys.path.append(str(_CORE_SRC))

from dataspace_control_plane_core.procedure_runtime.runtime_state import ProcedureRuntimeState
from dataspace_control_plane_core.procedure_runtime.workflow_contracts import ProcedureStatus


def test_runtime_state_defaults_to_empty_phase_and_zero_progress() -> None:
    state = ProcedureRuntimeState(status=ProcedureStatus.RUNNING)

    assert state.phase == ""
    assert state.progress_percent == 0
    assert state.search_attributes == {}
    assert state.links == {}


def test_runtime_state_accepts_stable_metadata_fields() -> None:
    state = ProcedureRuntimeState(
        status=ProcedureStatus.COMPLETED,
        phase="completed",
        progress_percent=100,
        search_attributes={"tenant_id": "tenant-a"},
        links={"poll_url": "/api/v1/operator/procedures/wf-1"},
    )

    assert state.status == ProcedureStatus.COMPLETED
    assert state.search_attributes["tenant_id"] == "tenant-a"
    assert state.links["poll_url"].endswith("/wf-1")
