from __future__ import annotations

import dataclasses
from typing import Any

import structlog
from dataspace_control_plane_procedures import (
    ProcedureDefinition as DiscoveredProcedureDefinition,
    discover_definitions,
)
from temporalio.common import WorkflowIDConflictPolicy, WorkflowIDReusePolicy

logger = structlog.get_logger(__name__)

ProcedureDefinition = DiscoveredProcedureDefinition


class ProcedureCatalog:
    def __init__(self, definitions: dict[str, ProcedureDefinition]) -> None:
        self._definitions = definitions

    @classmethod
    def discover(cls) -> "ProcedureCatalog":
        definitions = {
            definition.name: definition
            for definition in discover_definitions()
        }
        if not definitions:
            raise RuntimeError("Procedure discovery returned zero definitions")

        logger.info(
            "procedure_catalog.loaded",
            procedures=sorted(definitions),
            count=len(definitions),
        )
        return cls(definitions)

    def resolve(self, procedure_type: str) -> ProcedureDefinition:
        definition = self._definitions.get(procedure_type)
        if definition is None:
            raise ValueError(
                f"Unknown procedure type '{procedure_type}'. "
                f"Known types: {sorted(self._definitions)}"
            )
        return definition

    def available_types(self) -> list[str]:
        return sorted(self._definitions)

    def build_workflow_input(
        self,
        definition: ProcedureDefinition,
        *,
        tenant_id: str,
        legal_entity_id: str | None,
        payload: dict[str, Any],
        idempotency_key: str | None,
    ) -> Any:
        field_names = {field.name for field in dataclasses.fields(definition.start_input_type)}
        unknown_payload_keys = sorted(set(payload) - field_names)
        if unknown_payload_keys:
            raise ValueError(
                f"Unexpected payload field(s) for procedure '{definition.name}': "
                + ", ".join(unknown_payload_keys)
            )

        merged: dict[str, Any] = dict(payload)
        merged.setdefault("tenant_id", tenant_id)
        if legal_entity_id is not None:
            merged.setdefault("legal_entity_id", legal_entity_id)
        if idempotency_key is not None and "idempotency_key" in field_names:
            merged.setdefault("idempotency_key", idempotency_key)

        try:
            return definition.start_input_type(**merged)
        except TypeError as exc:
            raise ValueError(
                f"Invalid payload for procedure '{definition.name}': {exc}"
            ) from exc

    def build_workflow_id(
        self,
        definition: ProcedureDefinition,
        workflow_input: Any,
    ) -> str:
        values = {
            field.name: getattr(workflow_input, field.name)
            for field in dataclasses.fields(workflow_input)
        }
        try:
            return definition.manifest.workflow_id_template.format_map(values)
        except KeyError as exc:
            missing = exc.args[0]
            raise ValueError(
                f"Missing workflow id field '{missing}' for procedure '{definition.name}'"
            ) from exc

    def build_search_attributes(
        self,
        definition: ProcedureDefinition,
        workflow_input: Any,
    ) -> dict[str, list[str]]:
        values = {
            field.name: getattr(workflow_input, field.name)
            for field in dataclasses.fields(workflow_input)
        }
        attrs: dict[str, list[str]] = {}
        for key in definition.manifest.search_attribute_keys:
            if key == "procedure_type":
                attrs[key] = [definition.name]
            elif key == "status":
                attrs[key] = ["running"]
            else:
                value = values.get(key)
                if value not in (None, ""):
                    attrs[key] = [str(value)]
        return attrs

    def build_conflict_policy(
        self,
        definition: ProcedureDefinition,
    ) -> tuple[WorkflowIDConflictPolicy, WorkflowIDReusePolicy]:
        conflict_policy = definition.manifest.conflict_policy
        if conflict_policy == "use_existing":
            return (
                WorkflowIDConflictPolicy.USE_EXISTING,
                WorkflowIDReusePolicy.REJECT_DUPLICATE,
            )
        if conflict_policy == "reject":
            return (
                WorkflowIDConflictPolicy.FAIL,
                WorkflowIDReusePolicy.REJECT_DUPLICATE,
            )
        return (
            WorkflowIDConflictPolicy.UNSPECIFIED,
            WorkflowIDReusePolicy.ALLOW_DUPLICATE,
        )
