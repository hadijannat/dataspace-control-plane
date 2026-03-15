"""
Helm driver: thin subprocess wrapper for helm CLI operations.
Uses `helm upgrade --install` for idempotent releases.
All secrets must come from --set-file or --values pointing to vault-rendered files,
never as inline --set values.
"""
from __future__ import annotations
import subprocess
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


class HelmDriver:
    def __init__(self, kubeconfig: str | None = None, namespace: str = "default") -> None:
        self.kubeconfig = kubeconfig
        self.namespace = namespace

    def _run(self, args: list[str]) -> str:
        cmd = ["helm"] + args
        if self.kubeconfig:
            cmd = ["env", f"KUBECONFIG={self.kubeconfig}"] + cmd
        logger.debug("helm.exec", cmd=cmd)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            logger.error("helm.failed", stderr=result.stderr, cmd=cmd)
            raise RuntimeError(f"helm failed: {result.stderr.strip()}")
        return result.stdout

    def upgrade_install(
        self,
        release_name: str,
        chart: str,
        values_files: list[Path] | None = None,
        set_values: dict[str, str] | None = None,  # non-secret values only
        dry_run: bool = False,
        wait: bool = True,
    ) -> str:
        args = ["upgrade", "--install", release_name, chart, "--namespace", self.namespace, "--create-namespace"]
        for vf in (values_files or []):
            args += ["--values", str(vf)]
        for k, v in (set_values or {}).items():
            args += ["--set", f"{k}={v}"]
        if dry_run:
            args.append("--dry-run")
        if wait:
            args.append("--wait")
        logger.info("helm.upgrade_install", release=release_name, chart=chart, dry_run=dry_run)
        return self._run(args)

    def list_releases(self) -> str:
        return self._run(["list", "--namespace", self.namespace, "--output", "json"])

    def uninstall(self, release_name: str, dry_run: bool = False) -> str:
        args = ["uninstall", release_name, "--namespace", self.namespace]
        if dry_run:
            args.append("--dry-run")
        logger.warning("helm.uninstall", release=release_name, dry_run=dry_run)
        return self._run(args)
