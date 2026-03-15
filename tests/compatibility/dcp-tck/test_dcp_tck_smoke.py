"""
DCP TCK smoke tests.

These tests execute the pinned wrapper scripts in dry-run mode so the suite
verifies actor-specific orchestration without requiring live DCP services.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.compatibility

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DCP_TCK_DIR = REPO_ROOT / "tests" / "compatibility" / "dcp-tck"
LOCK_FILE = DCP_TCK_DIR / "lock.yaml"
CONFIG_DIR = DCP_TCK_DIR / "config"
REPORTS_DIR = DCP_TCK_DIR / "reports"
RUN_SCRIPT = REPO_ROOT / "tests" / "scripts" / "run_dcp_tck.sh"
ACTORS = {
    "credential-service": {
        "env_file": CONFIG_DIR / "credential-service.env",
        "env_var": "DCP_CREDENTIAL_SERVICE_URL",
        "url": "http://credential.example.test:8090",
        "report": REPORTS_DIR / "credential-service-report.xml",
        "command": REPORTS_DIR / "credential-service-command.txt",
        "log": REPORTS_DIR / "credential-service.log",
        "flag": "--credential-service-url",
        "protocols": "vpp,cip",
    },
    "issuer": {
        "env_file": CONFIG_DIR / "issuer.env",
        "env_var": "DCP_ISSUER_URL",
        "url": "http://issuer.example.test:8091",
        "report": REPORTS_DIR / "issuer-report.xml",
        "command": REPORTS_DIR / "issuer-command.txt",
        "log": REPORTS_DIR / "issuer.log",
        "flag": "--issuer-url",
        "protocols": "cip",
    },
    "verifier": {
        "env_file": CONFIG_DIR / "verifier.env",
        "env_var": "DCP_VERIFIER_URL",
        "url": "http://verifier.example.test:8092",
        "report": REPORTS_DIR / "verifier-report.xml",
        "command": REPORTS_DIR / "verifier-command.txt",
        "log": REPORTS_DIR / "verifier.log",
        "flag": "--verifier-url",
        "protocols": "vpp",
    },
}


def _lock_value(key: str) -> str:
    for line in LOCK_FILE.read_text().splitlines():
        if line.strip().startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def _reset_generated_artifacts() -> None:
    for actor in ACTORS.values():
        actor["env_file"].unlink(missing_ok=True)
        actor["report"].unlink(missing_ok=True)
        actor["command"].unlink(missing_ok=True)
        actor["log"].unlink(missing_ok=True)


@pytest.mark.compatibility
def test_dcp_tck_lock_pins_release_and_actor_matrix() -> None:
    lock_text = LOCK_FILE.read_text()
    assert _lock_value("tck_tag"), "lock.yaml must pin a non-empty tck_tag"
    assert _lock_value("tck_artifact") == "dcp-tck-runner"
    assert _lock_value("tck_source").endswith("/dcp-tck")
    assert "credential_service" in lock_text
    assert "issuer" in lock_text
    assert "verifier" in lock_text


@pytest.mark.compatibility
def test_dcp_tck_wrapper_dry_run_writes_actor_specific_reports() -> None:
    _reset_generated_artifacts()

    env = {**os.environ, "TCK_DRY_RUN": "1"}
    for actor in ACTORS.values():
        env[actor["env_var"]] = actor["url"]

    assert os.access(RUN_SCRIPT, os.X_OK), f"wrapper must be executable: {RUN_SCRIPT}"

    result = subprocess.run(
        ["bash", str(RUN_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout

    for actor_name, actor in ACTORS.items():
        env_file = actor["env_file"].read_text()
        assert f'{actor["env_var"]}={actor["url"]}' in env_file

        command_log = actor["command"].read_text()
        assert "dcp-tck-runner" in command_log
        assert actor["flag"] in command_log
        assert actor["url"] in command_log
        assert "--protocols" in command_log

        report_xml = actor["report"].read_text()
        assert f'testsuite name="dcp-tck-{actor_name}-dry-run"' in report_xml
        assert f'property name="tck_tag" value="{_lock_value("tck_tag")}"' in report_xml
        assert f'property name="protocols" value="{actor["protocols"]}"' in report_xml

        report_log = actor["log"].read_text()
        assert "dry-run" in report_log
        assert actor_name in report_log
