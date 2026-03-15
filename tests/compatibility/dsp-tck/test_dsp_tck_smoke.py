"""
tests/compatibility/dsp-tck/test_dsp_tck_smoke.py
DSP TCK smoke tests — verify TCK lock file, run scripts, and SUT configuration.

Tests run without requiring the SUT to be live.
Full TCK run: bash tests/scripts/run_dsp_tck.sh

Marker: compatibility
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.compatibility

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DSP_TCK_DIR = REPO_ROOT / "tests" / "compatibility" / "dsp-tck"
LOCK_FILE = DSP_TCK_DIR / "lock.yaml"
RUN_SCRIPT = REPO_ROOT / "tests" / "scripts" / "run_dsp_tck.sh"


# ---------------------------------------------------------------------------
# Test 1: lock.yaml exists
# ---------------------------------------------------------------------------


@pytest.mark.compatibility
def test_dsp_tck_lock_yaml_exists() -> None:
    """tests/compatibility/dsp-tck/lock.yaml must exist to pin the TCK version."""
    assert LOCK_FILE.exists(), (
        f"DSP TCK lock.yaml not found: {LOCK_FILE}\n"
        "Create it with tck_tag and tck_source fields to pin the TCK version."
    )


# ---------------------------------------------------------------------------
# Test 2: lock.yaml has version
# ---------------------------------------------------------------------------


@pytest.mark.compatibility
def test_dsp_tck_lock_has_version() -> None:
    """lock.yaml must contain a tck_tag: field."""
    if not LOCK_FILE.exists():
        pytest.skip("lock.yaml not found — skipping version check")

    content = LOCK_FILE.read_text()
    assert "tck_tag:" in content, (
        f"lock.yaml must contain 'tck_tag:' field. Contents:\n{content}"
    )

    # Extract tag value
    for line in content.splitlines():
        if line.strip().startswith("tck_tag:"):
            tag = line.split(":", 1)[1].strip().strip('"')
            assert tag, f"tck_tag must have a non-empty value, got: {line!r}"
            return

    pytest.fail("Could not find non-empty tck_tag value in lock.yaml")


# ---------------------------------------------------------------------------
# Test 3: Run script exists and is executable
# ---------------------------------------------------------------------------


@pytest.mark.compatibility
def test_dsp_tck_run_script_exists() -> None:
    """tests/scripts/run_dsp_tck.sh must exist and be executable."""
    assert RUN_SCRIPT.exists(), (
        f"DSP TCK run script not found: {RUN_SCRIPT}"
    )
    assert os.access(RUN_SCRIPT, os.X_OK), (
        f"DSP TCK run script must be executable: {RUN_SCRIPT}\n"
        "Run: chmod +x tests/scripts/run_dsp_tck.sh"
    )


# ---------------------------------------------------------------------------
# Test 4: DSP_SUT_BASEURL configured (skip if not set)
# ---------------------------------------------------------------------------


@pytest.mark.compatibility
def test_dsp_sut_url_configured() -> None:
    """If DSP_SUT_BASEURL env var is set, it must start with 'http'."""
    sut_url = os.environ.get("DSP_SUT_BASEURL", "")
    if not sut_url:
        pytest.skip("DSP_SUT_BASEURL not configured — SUT not available for TCK")

    assert sut_url.startswith("http"), (
        f"DSP_SUT_BASEURL must be an HTTP/HTTPS URL. Got: {sut_url!r}"
    )
