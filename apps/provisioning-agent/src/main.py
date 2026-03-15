"""
Provisioning agent CLI entry point.
Commands: bootstrap, plan, apply, reconcile.
"""
import asyncio
import typer
import structlog
import logging

from src.settings import settings

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(
        getattr(logging, settings.log_level.upper(), logging.INFO)
    )
)

app = typer.Typer(name="provisioning-agent", help="Declarative bootstrap and reconciliation agent.")


@app.command()
def bootstrap(
    dry_run: bool = typer.Option(False, "--dry-run", help="Print changes without applying"),
) -> None:
    """Create minimum prerequisites before control-api is live."""
    from src.commands.bootstrap import run_bootstrap
    asyncio.run(run_bootstrap(dry_run=dry_run))


@app.command()
def plan(
    desired_state_dir: str = typer.Option(settings.desired_state_dir, "--state-dir"),
) -> None:
    """Compute and display the diff between desired and actual state."""
    from src.commands.plan import run_plan
    asyncio.run(run_plan(desired_state_dir))


@app.command()
def apply(
    force: bool = typer.Option(False, "--force", help="Apply destructive changes"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Apply the provisioning plan."""
    from src.commands.plan import run_plan
    from src.commands.apply import run_apply

    async def _run() -> None:
        diff = await run_plan()
        await run_apply(diff, force=force, dry_run=dry_run)

    asyncio.run(_run())


@app.command()
def reconcile(
    interval: int = typer.Option(300, "--interval", help="Seconds between reconcile cycles"),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Run continuous reconciliation loop."""
    from src.commands.reconcile import run_reconcile
    asyncio.run(run_reconcile(interval_seconds=interval, dry_run=dry_run))


if __name__ == "__main__":
    app()
