"""
Terraform driver: subprocess wrapper for terraform CLI.
Handles init, plan (always), and apply. Never skips plan.
All secret inputs must come from TF_VAR_* env vars or -var-file with vault-rendered content.
"""
from __future__ import annotations
import subprocess
import structlog
from pathlib import Path

logger = structlog.get_logger(__name__)


class TerraformDriver:
    def __init__(self, working_dir: Path, env: dict[str, str] | None = None) -> None:
        self.working_dir = working_dir
        self.env = env or {}

    def _run(self, args: list[str], check: bool = True) -> subprocess.CompletedProcess:
        import os
        merged_env = {**os.environ, **self.env}
        cmd = ["terraform"] + args
        logger.debug("terraform.exec", cmd=cmd, cwd=str(self.working_dir))
        result = subprocess.run(cmd, cwd=self.working_dir, capture_output=True, text=True, timeout=600, env=merged_env)
        if check and result.returncode != 0:
            logger.error("terraform.failed", stderr=result.stderr, cmd=cmd)
            raise RuntimeError(f"terraform failed: {result.stderr.strip()}")
        return result

    def init(self, upgrade: bool = False) -> None:
        args = ["init", "-input=false"]
        if upgrade:
            args.append("-upgrade")
        self._run(args)
        logger.info("terraform.init_done", cwd=str(self.working_dir))

    def plan(self, var_file: Path | None = None, out: Path | None = None) -> str:
        args = ["plan", "-input=false", "-compact-warnings"]
        if var_file:
            args += [f"-var-file={var_file}"]
        if out:
            args += [f"-out={out}"]
        result = self._run(args)
        return result.stdout

    def apply(self, plan_file: Path | None = None, auto_approve: bool = False) -> str:
        args = ["apply", "-input=false", "-compact-warnings"]
        if plan_file:
            args += [str(plan_file)]
        elif auto_approve:
            args.append("-auto-approve")
        else:
            raise ValueError("Must pass plan_file or set auto_approve=True for terraform apply")
        result = self._run(args)
        logger.info("terraform.apply_done")
        return result.stdout

    def output(self, name: str | None = None) -> str:
        args = ["output", "-json"]
        if name:
            args.append(name)
        result = self._run(args)
        return result.stdout

    def validate(self) -> bool:
        result = self._run(["validate"], check=False)
        return result.returncode == 0
