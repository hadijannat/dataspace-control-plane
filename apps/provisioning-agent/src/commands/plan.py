"""
Plan command: compute and display the diff between desired and actual state.
Never modifies any resource. Exit 0 if no changes needed, 1 if changes pending.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import yaml
import structlog
from rich.console import Console
from rich.table import Table

from src.drivers.control_api import ControlApiDriver
from src.drivers.keycloak_admin import KeycloakAdminDriver
from src.drivers.kubernetes import KubernetesDriver
from src.settings import settings
from src.models.actual_state import ActualState, KeycloakRealmActual
from src.models.desired_state import DesiredState, KeycloakClientSpec, KeycloakRealmSpec
from src.models.diff import StateDiff, StateChange, ChangeSeverity
from src.state.checkpoints import CheckpointManager

logger = structlog.get_logger(__name__)
console = Console()
_IN_FLIGHT_STATUSES = {"STARTED", "RUNNING"}
_SUCCESS_STATUSES = _IN_FLIGHT_STATUSES | {"COMPLETED"}


def load_desired_state(desired_state_dir: str) -> DesiredState:
    state = DesiredState()
    root = Path(desired_state_dir)
    if not root.exists():
        logger.info("plan.desired_state_dir_missing", path=str(root))
        return state

    for path in sorted(root.rglob("*.y*ml")):
        document = yaml.safe_load(path.read_text()) or {}
        if not isinstance(document, dict):
            logger.warning("plan.invalid_manifest", path=str(path))
            continue

        for realm in document.get("keycloak_realms", []):
            clients = [KeycloakClientSpec(**client) for client in realm.get("clients", [])]
            state.keycloak_realms.append(
                KeycloakRealmSpec(
                    realm=realm["realm"],
                    display_name=realm.get("display_name", realm["realm"]),
                    enabled=realm.get("enabled", True),
                    clients=clients,
                )
            )

        state.edc_registrations.extend(document.get("edc_registrations", []))
        state.worker_namespaces.extend(document.get("worker_namespaces", []))
        state.tenant_bootstraps.extend(document.get("tenant_bootstraps", []))

    return state


async def discover_actual_state(desired: DesiredState) -> ActualState:
    actual = ActualState()
    checkpoints = CheckpointManager(settings.checkpoint_dir)

    try:
        kubernetes = KubernetesDriver()
    except Exception as exc:
        kubernetes = None
        logger.warning("plan.kubernetes_discovery_unavailable", error=str(exc))

    for namespace in desired.worker_namespaces:
        if kubernetes and kubernetes.namespace_exists(namespace):
            actual.worker_namespaces.append(namespace)

    if not desired.keycloak_realms:
        await _discover_control_plane_resources(desired, actual, checkpoints)
        return actual

    driver = KeycloakAdminDriver(
        base_url=settings.keycloak_url,
        realm=settings.keycloak_realm,
        client_id=settings.keycloak_admin_client_id,
        client_secret=settings.keycloak_admin_client_secret,
    )
    try:
        for realm in desired.keycloak_realms:
            try:
                realm_data = await driver.get_realm(realm.realm)
                if realm_data is None:
                    continue
                actual.keycloak_realms.append(
                    KeycloakRealmActual(
                        realm=realm.realm,
                        enabled=bool(realm_data.get("enabled", True)),
                        client_ids=await driver.list_client_ids(realm.realm),
                    )
                )
            except Exception as exc:
                logger.warning(
                    "plan.keycloak_discovery_failed",
                    realm=realm.realm,
                    error=str(exc),
                )
    finally:
        await driver.close()

    await _discover_control_plane_resources(desired, actual, checkpoints)
    return actual


async def _discover_control_plane_resources(
    desired: DesiredState,
    actual: ActualState,
    checkpoints: CheckpointManager,
) -> None:
    if not settings.control_api_url:
        return

    driver = ControlApiDriver(settings.control_api_url, settings.control_api_token)
    try:
        for index, registration in enumerate(desired.edc_registrations):
            identifier = registration.get("name") or registration.get("participant_id") or f"registration-{index}"
            checkpoint = checkpoints.load(f"edc_registration/{identifier}")
            if await _resource_is_present_via_control_api(driver, checkpoint):
                actual.edc_registrations.append(registration)

        for index, bootstrap in enumerate(desired.tenant_bootstraps):
            identifier = bootstrap.get("tenant_id") or bootstrap.get("name") or f"tenant-bootstrap-{index}"
            checkpoint = checkpoints.load(f"tenant_bootstrap/{identifier}")
            if await _resource_is_present_via_control_api(driver, checkpoint):
                actual.tenant_bootstraps.append(bootstrap)
    finally:
        await driver.close()


async def _resource_is_present_via_control_api(
    driver: ControlApiDriver,
    checkpoint: dict | None,
) -> bool:
    if not checkpoint:
        return False

    workflow_id = checkpoint.get("workflow_id")
    if not workflow_id:
        logger.warning("plan.legacy_checkpoint_ignored", checkpoint=checkpoint)
        return False

    try:
        status = await driver.get_procedure_status(workflow_id)
    except Exception as exc:
        logger.warning(
            "plan.control_api_discovery_failed",
            workflow_id=workflow_id,
            error=str(exc),
        )
        return False

    return status.get("status") in _SUCCESS_STATUSES


def compute_state_diff(desired: DesiredState, actual: ActualState) -> StateDiff:
    diff = StateDiff()
    actual_realms = {realm.realm: realm for realm in actual.keycloak_realms}

    for realm in desired.keycloak_realms:
        actual_realm = actual_realms.get(realm.realm)
        if actual_realm is None:
            diff.changes.append(
                StateChange(
                    resource_type="keycloak_realm",
                    resource_id=realm.realm,
                    operation="create",
                    severity=ChangeSeverity.SAFE,
                    description=f"Create Keycloak realm '{realm.realm}'",
                    details=asdict(realm),
                )
            )
        elif actual_realm.enabled != realm.enabled:
            diff.changes.append(
                StateChange(
                    resource_type="keycloak_realm",
                    resource_id=realm.realm,
                    operation="update",
                    severity=ChangeSeverity.REVIEW,
                    description=f"Update Keycloak realm '{realm.realm}' enabled state",
                    details=asdict(realm),
                )
            )

        actual_clients = set(actual_realm.client_ids if actual_realm else [])
        for client in realm.clients:
            if client.client_id not in actual_clients:
                diff.changes.append(
                    StateChange(
                        resource_type="keycloak_client",
                        resource_id=f"{realm.realm}/{client.client_id}",
                        operation="create",
                        severity=ChangeSeverity.SAFE,
                        description=f"Create Keycloak client '{client.client_id}' in realm '{realm.realm}'",
                        details={
                            "realm": realm.realm,
                            "spec": asdict(client),
                        },
                    )
                )

    for namespace in sorted(set(desired.worker_namespaces) - set(actual.worker_namespaces)):
        diff.changes.append(
            StateChange(
                resource_type="k8s_namespace",
                resource_id=namespace,
                operation="create",
                severity=ChangeSeverity.REVIEW,
                description=f"Declare worker namespace '{namespace}' for downstream infra convergence",
                details={"namespace": namespace},
            )
        )

    for index, registration in enumerate(desired.edc_registrations):
        identifier = registration.get("name") or registration.get("participant_id") or f"registration-{index}"
        if registration not in actual.edc_registrations:
            diff.changes.append(
                StateChange(
                    resource_type="edc_registration",
                    resource_id=str(identifier),
                    operation="create",
                    severity=ChangeSeverity.REVIEW,
                    description=f"Register EDC participant '{identifier}'",
                    details=registration,
                )
            )

    for index, bootstrap in enumerate(desired.tenant_bootstraps):
        identifier = bootstrap.get("tenant_id") or bootstrap.get("name") or f"tenant-bootstrap-{index}"
        if bootstrap not in actual.tenant_bootstraps:
            diff.changes.append(
                StateChange(
                    resource_type="tenant_bootstrap",
                    resource_id=str(identifier),
                    operation="create",
                    severity=ChangeSeverity.REVIEW,
                    description=f"Bootstrap tenant manifest '{identifier}' through the control plane",
                    details=bootstrap,
                )
            )

    return diff


async def run_plan(desired_state_dir: str | None = None) -> StateDiff:
    """Compute the diff and print it. Returns the diff for use by apply."""
    logger.info("plan.start")
    desired_dir = desired_state_dir or settings.desired_state_dir
    desired = load_desired_state(desired_dir)
    actual = await discover_actual_state(desired)
    diff = compute_state_diff(desired, actual)

    table = Table(title="Provisioning Plan")
    table.add_column("Resource")
    table.add_column("Operation")
    table.add_column("Severity")
    table.add_column("Description")

    for change in diff.changes:
        color = {"safe": "green", "review": "yellow", "destructive": "red"}.get(change.severity, "white")
        table.add_row(
            f"{change.resource_type}/{change.resource_id}",
            change.operation,
            f"[{color}]{change.severity}[/{color}]",
            change.description,
        )

    console.print(table)
    if not diff.has_changes:
        console.print("[green]No changes required.[/green]")
    else:
        console.print(f"[bold]Summary:[/bold] {diff.summary()}")
        if diff.has_destructive:
            console.print("[red bold]WARNING: Destructive changes detected. Use --force to apply.[/red bold]")

    return diff
