from __future__ import annotations
from dataspace_control_plane_core.domains._shared.ids import AggregateId
from dataspace_control_plane_core.domains._shared.time import Clock, UtcClock
from .commands import TriggerGapScanCommand, RecordScanResultCommand
from .events import GapScanTriggered, GapScanCompleted, CompliancePostureChanged
from .model.aggregates import ComplianceRecord
from .model.enums import CompliancePosture
from .model.invariants import require_non_empty_scope
from .ports import ComplianceRecordRepository, GapScannerPort


class ComplianceService:
    def __init__(self, repo: ComplianceRecordRepository, clock: Clock = UtcClock()) -> None:
        self._repo = repo
        self._clock = clock

    async def trigger_scan(self, cmd: TriggerGapScanCommand) -> ComplianceRecord:
        """
        Trigger a gap scan, execute it via the scanner port, and persist the result.
        Creates a new ComplianceRecord if one does not yet exist for the legal entity.
        """
        require_non_empty_scope(cmd.scope)

        existing = await self._repo.find_by_legal_entity(cmd.tenant_id, cmd.legal_entity_id)
        if existing is None:
            record = ComplianceRecord(
                id=AggregateId.generate(),
                tenant_id=cmd.tenant_id,
                legal_entity_id=cmd.legal_entity_id,
            )
            expected_version = 0
        else:
            record = existing
            expected_version = record.version

        record._raise_event(GapScanTriggered(
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
            framework_count=len(cmd.scope.frameworks),
        ))
        await self._repo.save(record, expected_version=expected_version)
        return record

    async def record_result(self, cmd: RecordScanResultCommand) -> ComplianceRecord:
        """Record an externally-computed scan result (e.g. from a Temporal activity)."""
        existing = await self._repo.find_by_legal_entity(cmd.tenant_id, cmd.legal_entity_id)
        if existing is None:
            record = ComplianceRecord(
                id=AggregateId.generate(),
                tenant_id=cmd.tenant_id,
                legal_entity_id=cmd.legal_entity_id,
            )
            expected_version = 0
        else:
            record = existing
            expected_version = record.version

        previous_posture = record.current_posture
        record.record_scan(cmd.snapshot)

        record._raise_event(GapScanCompleted(
            tenant_id=cmd.tenant_id,
            legal_entity_id=cmd.legal_entity_id,
            gap_count=len(cmd.snapshot.gaps),
            posture=cmd.snapshot.posture,
        ))

        if previous_posture != record.current_posture:
            record._raise_event(CompliancePostureChanged(
                tenant_id=cmd.tenant_id,
                legal_entity_id=cmd.legal_entity_id,
                previous_posture=previous_posture,
                new_posture=record.current_posture,
            ))

        await self._repo.save(record, expected_version=expected_version)
        return record
