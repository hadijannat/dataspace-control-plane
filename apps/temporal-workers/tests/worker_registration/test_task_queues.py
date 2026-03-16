"""Verify all expected task queues are declared."""
from dataspace_control_plane_temporal_workers.bootstrap.task_queues import (
    ALL_QUEUES,
    ONBOARDING,
    MACHINE_TRUST,
    TWINS_PUBLICATION,
    CONTRACTS_NEGOTIATION,
    COMPLIANCE,
    MAINTENANCE,
)


def test_all_queues_declared():
    expected = {ONBOARDING, MACHINE_TRUST, TWINS_PUBLICATION, CONTRACTS_NEGOTIATION, COMPLIANCE, MAINTENANCE}
    assert set(ALL_QUEUES) == expected
