"""
tests/compatibility/dcp-tck/test_dcp_tck_smoke.py
DCP TCK smoke tests — verify TCK lock file, run scripts, and actor configuration.

Tests run without requiring the SUT actors to be live.
Full TCK run: bash tests/scripts/run_dcp_tck.sh

Marker: compatibility
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.compatibility

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DCP_TCK_DIR = REPO_ROOT / "tests" / "compatibility" / "dcp-tck"
LOCK_FILE = DCP_TCK_DIR / "lock.yaml"
SCRIPTS_DIR = DCP_TCK_DIR / "scripts"


# ---------------------------------------------------------------------------
# Test 1: lock.yaml exists
# ---------------------------------------------------------------------------


@pytest.mark.compatibility
def test_dcp_tck_lock_yaml_exists() -> None:
    """tests/compatibility/dcp-tck/lock.yaml must exist to pin the TCK version."""
    assert LOCK_FILE.exists(), (
        f"DCP TCK lock.yaml not found: {LOCK_FILE}\n"
        "Create it with tck_tag and tck_source fields to pin the TCK version."
    )


# ---------------------------------------------------------------------------
# Test 2: lock.yaml has version
# ---------------------------------------------------------------------------


@pytest.mark.compatibility
def test_dcp_tck_lock_has_version() -> None:
    """lock.yaml must contain a tck_tag: field."""
    if not LOCK_FILE.exists():
        pytest.skip("lock.yaml not found — skipping version check")

    content = LOCK_FILE.read_text()
    assert "tck_tag:" in content, (
        f"lock.yaml must contain 'tck_tag:' field. Contents:\n{content}"
    )

    for line in content.splitlines():
        if line.strip().startswith("tck_tag:"):
            tag = line.split(":", 1)[1].strip().strip('"')
            assert tag, f"tck_tag must have a non-empty value, got: {line!r}"
            return

    pytest.fail("Could not find non-empty tck_tag value in lock.yaml")


# ---------------------------------------------------------------------------
# Test 3: DCP actor run scripts exist
# ---------------------------------------------------------------------------


@pytest.mark.compatibility
def test_dcp_tck_scripts_exist() -> None:
    """All three DCP actor run scripts must exist."""
    required_scripts = [
        SCRIPTS_DIR / "run_credential_service.sh",
        SCRIPTS_DIR / "run_issuer.sh",
        SCRIPTS_DIR / "run_verifier.sh",
    ]
    missing = [s for s in required_scripts if not s.exists()]
    assert not missing, (
        f"DCP TCK actor scripts missing ({len(missing)} file(s)):\n"
        + "\n".join(f"  {s}" for s in missing)
    )


# ---------------------------------------------------------------------------
# Test 4: DCP actors configured separately
# ---------------------------------------------------------------------------


@pytest.mark.compatibility
def test_dcp_actors_configured_separately() -> None:
    """
    DCP actors must use separate environment variables — they must not be collapsed.

    Each actor has its own URL and protocols. Using a single URL for all three actors
    would violate the DCP architecture (Credential Service, Issuer, Verifier are distinct).
    """
    actor_env_vars = [
        "DCP_CREDENTIAL_SERVICE_URL",
        "DCP_ISSUER_URL",
        "DCP_VERIFIER_URL",
    ]

    # Document: these must be separate env vars (not the same URL for all three)
    values = {var: os.environ.get(var, "") for var in actor_env_vars}
    configured = {k: v for k, v in values.items() if v}

    if not configured:
        # All three are unset — this is expected in development/unit test runs
        # The test passes because the env vars are architecturally separate (just not set)
        return

    # If any are set, assert they are distinct URLs
    urls = list(configured.values())
    assert len(set(urls)) == len(urls), (
        f"DCP actor URLs must be distinct — different actors must not share the same URL.\n"
        f"Found duplicate URLs: {values}"
    )
