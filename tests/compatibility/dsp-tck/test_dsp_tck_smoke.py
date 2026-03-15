"""
DSP TCK smoke tests.

These tests validate the pinned wrapper wiring without requiring a live DSP SUT
or downloading the official runner. Full protocol conformance remains owned by
the runtime harness outside this directory.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.compatibility

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DSP_TCK_DIR = REPO_ROOT / "tests" / "compatibility" / "dsp-tck"
LOCK_FILE = DSP_TCK_DIR / "lock.yaml"
CONFIG_DIR = DSP_TCK_DIR / "config"
REPORTS_DIR = DSP_TCK_DIR / "reports"
RUN_SCRIPT = REPO_ROOT / "tests" / "scripts" / "run_dsp_tck.sh"


def _lock_value(key: str) -> str:
    for line in LOCK_FILE.read_text().splitlines():
        if line.strip().startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return ""


def _reset_generated_artifacts() -> None:
    for generated in (
        CONFIG_DIR / "sut.env",
        REPORTS_DIR / "command.txt",
        REPORTS_DIR / "report.log",
        REPORTS_DIR / "report.xml",
    ):
        generated.unlink(missing_ok=True)


@pytest.mark.compatibility
def test_dsp_tck_lock_pins_release_metadata() -> None:
    assert LOCK_FILE.exists(), f"missing DSP TCK lock file: {LOCK_FILE}"
    assert _lock_value("tck_tag"), "lock.yaml must pin a non-empty tck_tag"
    assert _lock_value("tck_artifact") == "dsp-tck-runner"
    assert _lock_value("tck_source").endswith("/dsp-tck")


@pytest.mark.compatibility
def test_dsp_tck_wrapper_dry_run_writes_config_and_reports() -> None:
    _reset_generated_artifacts()

    env = {
        **os.environ,
        "DSP_SUT_BASEURL": "http://sut.example.test:19191",
        "DSP_SUT_IDENTITY_URL": "http://identity.example.test:18181",
        "TCK_DRY_RUN": "1",
    }

    result = subprocess.run(
        ["bash", str(RUN_SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    assert os.access(RUN_SCRIPT, os.X_OK), f"wrapper must be executable: {RUN_SCRIPT}"

    sut_env = (CONFIG_DIR / "sut.env").read_text()
    assert "DSP_SUT_BASEURL=http://sut.example.test:19191" in sut_env
    assert "DSP_SUT_IDENTITY_URL=http://identity.example.test:18181" in sut_env

    command_log = (REPORTS_DIR / "command.txt").read_text()
    assert "dsp-tck-runner" in command_log
    assert "--sut-base-url" in command_log
    assert "--identity-url" in command_log
    assert "http://sut.example.test:19191" in command_log
    assert "http://identity.example.test:18181" in command_log

    report_xml = (REPORTS_DIR / "report.xml").read_text()
    assert 'testsuite name="dsp-tck-dry-run"' in report_xml
    assert f'property name="tck_tag" value="{_lock_value("tck_tag")}"' in report_xml
    assert 'property name="mode" value="dry-run"' in report_xml

    report_log = (REPORTS_DIR / "report.log").read_text()
    assert "dry-run" in report_log
    assert "DSP TCK" in report_log
