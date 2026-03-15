"""
Bootstrap command: create minimum prerequisites before control-api is live.
Runs once — not idempotent in the loop sense, but each step is check-before-create.
"""
import structlog
from src.commands.plan import run_plan
from src.commands.apply import run_apply

logger = structlog.get_logger(__name__)


async def run_bootstrap(dry_run: bool = False) -> None:
    """Create realm, initial clients/roles, service accounts, and environment descriptors."""
    logger.info("bootstrap.start", dry_run=dry_run)
    diff = await run_plan()
    await run_apply(diff, dry_run=dry_run)
    logger.info("bootstrap.complete")
