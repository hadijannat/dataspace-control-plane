"""
Apply command: execute the plan (create/update resources).
Requires an explicit diff to be computed first.
Irreversible operations require --force.
"""
import structlog
from src.models.diff import StateDiff, ChangeSeverity
from src.settings import settings
from src.state.checkpoints import CheckpointManager
from src.state.locks import file_lock

logger = structlog.get_logger(__name__)


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
                await _dispatch_change(change)
                if change.operation == "delete":
                    checkpoints.delete(key)
                else:
                    checkpoints.save(key, change.details)


async def _dispatch_change(change) -> None:
    """Dispatch a single change to the appropriate driver."""
    import structlog
    log = structlog.get_logger(__name__)
    rt = change.resource_type.lower()
    if rt in ("keycloak_realm", "keycloak_client", "keycloak_role"):
        await _apply_keycloak(change)
    elif rt in ("helm_release",):
        await _apply_helm(change)
    elif rt in ("terraform_resource",):
        await _apply_terraform(change)
    elif rt in ("k8s_namespace", "k8s_secret"):
        await _apply_kubernetes(change)
    elif rt in ("edc_registration", "tenant_bootstrap"):
        log.info("apply.deferred_to_control_plane", resource_type=change.resource_type, resource_id=change.resource_id)
    else:
        log.warning("apply.unknown_resource_type", resource_type=change.resource_type, resource_id=change.resource_id)


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
    # KubernetesDriver.ensure_namespace() or ensure_secret()
