from __future__ import annotations

import dataclasses
import hashlib
import json

from dataspace_control_plane_adapters.infrastructure.postgres.api import (
    PostgresAuditSink,
    PostgresIdempotencyRepository,
    PostgresProcedureRuntimeRepository,
)
from dataspace_control_plane_core.audit.records import (
    AuditCategory,
    AuditOutcome,
    AuditRecord,
)
from dataspace_control_plane_core.domains._shared.actor import ActorRef, ActorType
from dataspace_control_plane_core.domains._shared.correlation import CorrelationContext
from dataspace_control_plane_core.domains._shared.ids import LegalEntityId, TenantId, WorkflowId

from app.application.dto.procedures import ProcedureHandleDTO
from app.auth.principals import Principal
from app.services.procedure_catalog import ProcedureCatalog
from app.services.temporal_gateway import TemporalGateway


class IdempotencyConflictError(Exception):
    """Raised when a scoped idempotency key is reused with a different fingerprint."""


class StartProcedureService:
    def __init__(
        self,
        *,
        catalog: ProcedureCatalog,
        gateway: TemporalGateway,
        idempotency_repository: PostgresIdempotencyRepository,
        procedure_runtime_repository: PostgresProcedureRuntimeRepository,
        audit_sink: PostgresAuditSink,
    ) -> None:
        self._catalog = catalog
        self._gateway = gateway
        self._idempotency_repository = idempotency_repository
        self._procedure_runtime_repository = procedure_runtime_repository
        self._audit_sink = audit_sink

    async def start(
        self,
        *,
        procedure_type: str,
        tenant_id: str,
        legal_entity_id: str | None,
        payload: dict,
        idempotency_key: str | None,
        principal: Principal,
        correlation_id: str | None,
        poll_url_template: str,
        audit_event_type: str,
    ) -> ProcedureHandleDTO:
        if not principal.can_access_tenant(tenant_id):
            raise PermissionError(f"Access to tenant '{tenant_id}' is not permitted")

        definition = self._catalog.resolve(procedure_type)
        workflow_input = self._catalog.build_workflow_input(
            definition,
            tenant_id=tenant_id,
            legal_entity_id=legal_entity_id,
            payload=payload,
            idempotency_key=idempotency_key,
        )
        workflow_id = self._catalog.build_workflow_id(definition, workflow_input)
        search_attributes = self._catalog.build_search_attributes(definition, workflow_input)

        accepted = ProcedureHandleDTO(
            workflow_id=workflow_id,
            procedure_type=procedure_type,
            tenant_id=tenant_id,
            status="running",
            poll_url=poll_url_template.format(workflow_id=workflow_id),
            stream_url=f"/api/v1/streams/workflows/{workflow_id}",
            correlation_id=correlation_id,
        )

        if idempotency_key:
            acquisition = await self._idempotency_repository.acquire(
                tenant_id=tenant_id,
                procedure_type=procedure_type,
                idempotency_key=idempotency_key,
                request_fingerprint=_fingerprint_request(
                    procedure_type=procedure_type,
                    workflow_input=workflow_input,
                    principal=principal,
                ),
                workflow_id=workflow_id,
                response_json=accepted.model_dump(mode="json"),
                status=accepted.status,
            )
            if acquisition.outcome == "conflict":
                raise IdempotencyConflictError(
                    f"Idempotency key '{idempotency_key}' conflicts with an existing request"
                )
            if acquisition.outcome == "replay":
                return ProcedureHandleDTO(**acquisition.record.response_json)

        try:
            started = await self._gateway.start_definition(
                definition=definition,
                workflow_input=workflow_input,
                workflow_id=workflow_id,
                search_attributes=search_attributes,
            )
        except Exception:
            if idempotency_key:
                await self._idempotency_repository.release(
                    tenant_id=tenant_id,
                    procedure_type=procedure_type,
                    idempotency_key=idempotency_key,
                )
            raise

        if idempotency_key:
            await self._idempotency_repository.finalize(
                tenant_id=tenant_id,
                procedure_type=procedure_type,
                idempotency_key=idempotency_key,
                run_id=started.run_id,
                response_json=accepted.model_dump(mode="json"),
                status=accepted.status,
            )

        await self._procedure_runtime_repository.upsert_state(
            workflow_id=workflow_id,
            procedure_type=procedure_type,
            tenant_id=tenant_id,
            status=accepted.status,
            phase="accepted",
            progress_percent=0,
            search_attributes=search_attributes,
            links={
                "poll_url": accepted.poll_url,
                "stream_url": accepted.stream_url,
            },
            result=None,
            failure_message=None,
        )

        audit_record = AuditRecord.new(
            tenant_id=TenantId(tenant_id),
            category=AuditCategory.ADMIN,
            action=audit_event_type,
            outcome=AuditOutcome.SUCCESS,
            actor=ActorRef(
                subject=principal.subject,
                actor_type=ActorType.HUMAN,
                tenant_id=TenantId(tenant_id),
                display_name=principal.email,
            ),
            correlation=CorrelationContext.new(
                workflow_id=WorkflowId(workflow_id),
                request_id=correlation_id,
            ),
            subject_id=workflow_id,
            subject_type="procedure",
            legal_entity_id=LegalEntityId(legal_entity_id) if legal_entity_id else None,
            detail={
                "procedure_type": procedure_type,
                "correlation_id": correlation_id,
                "idempotency_key": idempotency_key,
                "run_id": started.run_id,
            },
        )
        await self._audit_sink.emit(audit_record)
        return accepted


def _fingerprint_request(
    *,
    procedure_type: str,
    workflow_input: object,
    principal: Principal,
) -> str:
    payload = {
        "procedure_type": procedure_type,
        "workflow_input": dataclasses.asdict(workflow_input),
        "principal": {
            "subject": principal.subject,
            "tenant_ids": sorted(principal.tenant_ids),
        },
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode()).hexdigest()
