"""
Apply command: execute the plan (create/update resources).
Requires an explicit diff to be computed first.
Irreversible operations require --force.
"""
from __future__ import annotations

from dataclasses import dataclass

import structlog
from src.drivers.control_api import ControlApiDriver
from src.models.diff import StateDiff
from src.settings import settings
from src.state.checkpoints import CheckpointManager
from src.state.locks import file_lock

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class DispatchResult:
    checkpoint_data: dict | None = None


async def run_apply(diff: StateDiff, force: bool = False, dry_run: bool = False) -> None:
    if not diff.has_changes:
        logger.info("apply.no_changes")
        return

    if diff.has_destructive and not force:
        raise RuntimeError(
            "Destructive changes detected. Re-run with --force to apply. "
            "Review the plan output carefully before proceeding."
        )

    checkpoints = CheckpointManager(settings.checkpoint_dir)
    for change in diff.changes:
        if change.operation == "noop":
            continue
        key = f"{change.resource_type}/{change.resource_id}"
        if checkpoints.load(key) == change.details and change.operation != "delete":
            logger.info("apply.skip_checkpointed", resource=key)
            continue
        logger.info(
            "apply.change",
            resource=key,
            op=change.operation,
            dry_run=dry_run,
        )
        with file_lock(key.replace("/", "_")):
            if not dry_run:
                result = await _dispatch_change(change)
                if change.operation == "delete":
                    checkpoints.delete(key)
                elif result.checkpoint_data is not None:
                    checkpoints.save(key, result.checkpoint_data)


async def _dispatch_change(change) -> DispatchResult:
    """Dispatch a single change to the appropriate driver."""
    import structlog
    log = structlog.get_logger(__name__)
    rt = change.resource_type.lower()
    if rt in ("keycloak_realm", "keycloak_client", "keycloak_role"):
        await _apply_keycloak(change)
        return DispatchResult(checkpoint_data=change.details)
    if rt in ("helm_release",):
        await _apply_helm(change)
        return DispatchResult(checkpoint_data=change.details)
    if rt in ("terraform_resource",):
        await _apply_terraform(change)
        return DispatchResult(checkpoint_data=change.details)
    if rt in ("k8s_namespace", "k8s_secret"):
        await _apply_kubernetes(change)
        return DispatchResult(checkpoint_data=change.details)
    if rt in ("edc_registration", "tenant_bootstrap"):
        return await _dispatch_control_plane_change(change)
    raise RuntimeError(
        f"Unknown resource type '{change.resource_type}' for change '{change.resource_id}'"
    )


async def _dispatch_control_plane_change(change) -> DispatchResult:
    procedure_type = change.details.get("procedure_type") or _default_procedure_type(change.resource_type)
    tenant_id = change.details.get("tenant_id")
    if not tenant_id:
        raise RuntimeError(
            f"{change.resource_type} '{change.resource_id}' is missing tenant_id and cannot be routed via control-api"
        )

    driver = ControlApiDriver(settings.control_api_url, settings.control_api_token)
    try:
        response = await driver.start_procedure(
            {
                "procedure_type": procedure_type,
                "tenant_id": tenant_id,
                "legal_entity_id": change.details.get("legal_entity_id"),
                "payload": change.details,
                "idempotency_key": change.details.get("idempotency_key") or f"{change.resource_type}:{change.resource_id}",
            }
        )
    finally:
        await driver.close()

    return DispatchResult(
        checkpoint_data={
            "resource_type": change.resource_type,
            "resource_id": change.resource_id,
            "resource": change.details,
            **response,
        }
    )


def _default_procedure_type(resource_type: str) -> str:
    defaults = {
        "tenant_bootstrap": "company-onboarding",
        "edc_registration": "connector-bootstrap",
    }
    return defaults[resource_type]


async def _apply_keycloak(change) -> None:
    from src.drivers.keycloak_admin import KeycloakAdminDriver
    import structlog
    log = structlog.get_logger(__name__)
    log.info("apply.keycloak", op=change.operation, resource=change.resource_id)
    driver = KeycloakAdminDriver(
        base_url=settings.keycloak_url,
        realm=settings.keycloak_realm,
        client_id=settings.keycloak_admin_client_id,
        client_secret=settings.keycloak_admin_client_secret,
    )
    try:
        if change.resource_type == "keycloak_realm" and change.operation in {"create", "update"}:
            await driver.create_realm(
                realm=change.details["realm"],
                display_name=change.details["display_name"],
                enabled=change.details.get("enabled", True),
            )
        elif change.resource_type == "keycloak_client" and change.operation == "create":
            spec = change.details["spec"]
            await driver.create_client(
                realm=change.details["realm"],
                spec={
                    "clientId": spec["client_id"],
                    "name": spec["name"],
                    "protocol": spec.get("protocol", "openid-connect"),
                    "publicClient": spec.get("public_client", False),
                    "redirectUris": spec.get("redirect_uris", []),
                },
            )
    finally:
        await driver.close()


async def _apply_helm(change) -> None:
    from src.drivers.helm import HelmDriver
    import structlog
    log = structlog.get_logger(__name__)
    log.info("apply.helm", op=change.operation, resource=change.resource_id)
    # HelmDriver.upgrade_install(release_name=..., chart=..., values_files=[...])


async def _apply_terraform(change) -> None:
    from src.drivers.terraform import TerraformDriver
    import structlog
    log = structlog.get_logger(__name__)
    log.info("apply.terraform", op=change.operation, resource=change.resource_id)
    # TerraformDriver.init() then plan() then apply(plan_file=...)


async def _apply_kubernetes(change) -> None:
    from src.drivers.kubernetes import KubernetesDriver
    import structlog
    log = structlog.get_logger(__name__)
    log.info("apply.kubernetes", op=change.operation, resource=change.resource_id)
    driver = KubernetesDriver()
    if change.resource_type == "k8s_namespace" and change.operation in {"create", "update"}:
        driver.ensure_namespace(change.details["namespace"])
    elif change.resource_type == "k8s_secret" and change.operation in {"create", "update"}:
        driver.ensure_secret(
            namespace=change.details["namespace"],
            name=change.details["name"],
            data=change.details["data"],
            secret_type=change.details.get("secret_type", "Opaque"),
        )
