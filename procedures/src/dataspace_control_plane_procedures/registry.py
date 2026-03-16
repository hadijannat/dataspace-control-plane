"""Canonical procedure definition registry.

Each procedure package exports one explicit ``definition`` object from its
``api.py`` module. Runtime owners consume these definitions directly rather
than rediscovering manifests, dataclasses, or registrations through reflection.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from dataspace_control_plane_procedures._shared.manifests import ProcedureManifest
from dataspace_control_plane_procedures._shared.task_queues import (
    COMPLIANCE_QUEUE,
    CONTRACTS_NEGOTIATION_QUEUE,
    MACHINE_TRUST_QUEUE,
    MAINTENANCE_QUEUE,
    ONBOARDING_QUEUE,
    TWINS_PUBLICATION_QUEUE,
)


@dataclass(frozen=True)
class ProcedureDefinition:
    """Static runtime wiring contract for one procedure family."""

    name: str
    module_name: str
    manifest: ProcedureManifest
    start_input_type: type[Any]
    status_query_type: type[Any] | None
    workflow_types: tuple[Any, ...]
    activity_functions: tuple[Any, ...]
    query_name: str = "get_status"

    @property
    def task_queue(self) -> str:
        return self.manifest.task_queue

    @property
    def workflow_type(self) -> str:
        return self.manifest.workflow_type


def build_definition(
    *,
    api_module_name: str,
    manifest: ProcedureManifest,
    start_input_type: type[Any],
    workflow_types: list[Any] | tuple[Any, ...],
    activity_functions: list[Any] | tuple[Any, ...],
    status_query_type: type[Any] | None = None,
    query_name: str = "get_status",
) -> ProcedureDefinition:
    """Build a canonical definition from a procedure ``api.py`` module."""
    module_name = api_module_name.split(".")[-2]
    return ProcedureDefinition(
        name=module_name.replace("_", "-"),
        module_name=module_name,
        manifest=manifest,
        start_input_type=start_input_type,
        status_query_type=status_query_type,
        workflow_types=tuple(workflow_types),
        activity_functions=tuple(activity_functions),
        query_name=query_name,
    )


def _load_api_modules() -> tuple[Any, ...]:
    from dataspace_control_plane_procedures.company_onboarding import api as company_onboarding_api
    from dataspace_control_plane_procedures.connector_bootstrap import api as connector_bootstrap_api
    from dataspace_control_plane_procedures.delegate_tenant import api as delegate_tenant_api
    from dataspace_control_plane_procedures.dpp_provision import api as dpp_provision_api
    from dataspace_control_plane_procedures.evidence_export import api as evidence_export_api
    from dataspace_control_plane_procedures.negotiate_contract import api as negotiate_contract_api
    from dataspace_control_plane_procedures.publish_asset import api as publish_asset_api
    from dataspace_control_plane_procedures.register_digital_twin import api as register_digital_twin_api
    from dataspace_control_plane_procedures.revoke_credentials import api as revoke_credentials_api
    from dataspace_control_plane_procedures.rotate_credentials import api as rotate_credentials_api
    from dataspace_control_plane_procedures.wallet_bootstrap import api as wallet_bootstrap_api

    return (
        company_onboarding_api,
        connector_bootstrap_api,
        delegate_tenant_api,
        dpp_provision_api,
        evidence_export_api,
        negotiate_contract_api,
        publish_asset_api,
        register_digital_twin_api,
        revoke_credentials_api,
        rotate_credentials_api,
        wallet_bootstrap_api,
    )


_DISCOVERED_DEFINITIONS: tuple[ProcedureDefinition, ...] | None = None


def discover_definitions() -> tuple[ProcedureDefinition, ...]:
    """Return every registered procedure definition.

    Raises ``RuntimeError`` when no procedures are exported or names collide.
    """
    global _DISCOVERED_DEFINITIONS
    if _DISCOVERED_DEFINITIONS is not None:
        return _DISCOVERED_DEFINITIONS

    definitions = tuple(api.definition for api in _load_api_modules())
    if not definitions:
        raise RuntimeError("No procedure definitions were exported by dataspace_control_plane_procedures")

    seen: set[str] = set()
    duplicates: list[str] = []
    for definition in definitions:
        if definition.name in seen:
            duplicates.append(definition.name)
        seen.add(definition.name)
    if duplicates:
        raise RuntimeError(
            "Duplicate procedure definitions exported: " + ", ".join(sorted(set(duplicates)))
        )

    _DISCOVERED_DEFINITIONS = definitions
    return definitions


def get_definition(name: str) -> ProcedureDefinition:
    for definition in discover_definitions():
        if definition.name == name:
            return definition
    raise KeyError(name)


WORKFLOW_REGISTRY: dict[str, list[Any]] = {
    ONBOARDING_QUEUE: [],
    MACHINE_TRUST_QUEUE: [],
    TWINS_PUBLICATION_QUEUE: [],
    CONTRACTS_NEGOTIATION_QUEUE: [],
    COMPLIANCE_QUEUE: [],
    MAINTENANCE_QUEUE: [],
}

ACTIVITY_REGISTRY: dict[str, list[Any]] = {
    ONBOARDING_QUEUE: [],
    MACHINE_TRUST_QUEUE: [],
    TWINS_PUBLICATION_QUEUE: [],
    CONTRACTS_NEGOTIATION_QUEUE: [],
    COMPLIANCE_QUEUE: [],
    MAINTENANCE_QUEUE: [],
}

_POPULATED = False


def _register_definition(definition: ProcedureDefinition) -> None:
    workflows = WORKFLOW_REGISTRY.setdefault(definition.task_queue, [])
    activities = ACTIVITY_REGISTRY.setdefault(definition.task_queue, [])
    for workflow in definition.workflow_types:
        if workflow not in workflows:
            workflows.append(workflow)
    for activity in definition.activity_functions:
        if activity not in activities:
            activities.append(activity)


def reset_registry() -> None:
    global _POPULATED
    for registry in (WORKFLOW_REGISTRY, ACTIVITY_REGISTRY):
        for items in registry.values():
            items.clear()
    _POPULATED = False


def populate_from_procedures() -> None:
    """Populate queue registries from explicit procedure definitions."""
    global _POPULATED
    if _POPULATED:
        return
    for definition in discover_definitions():
        _register_definition(definition)
    _POPULATED = True


def verify_registry() -> None:
    """Log a warning for any queue with no registered workflows. Never raises."""
    import warnings

    for queue, workflows in WORKFLOW_REGISTRY.items():
        if not workflows:
            warnings.warn(
                f"Task queue '{queue}' has no registered workflows. "
                "Ensure discover_definitions() exports a procedure for this queue.",
                stacklevel=2,
            )
