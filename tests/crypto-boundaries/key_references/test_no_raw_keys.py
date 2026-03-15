"""
tests/crypto-boundaries/key_references/test_no_raw_keys.py
Verifies that no raw private key material exists in the repository.

Invariants:
- No .pem or .key files committed to the repo
- No private key PEM headers in any file
- No private key fields in schema examples
- No raw key material in test data
- Vault Transit keys created without exportable=True cannot be exported

Tests 1-3 are static scans that run without any services.
Test 4 requires vault_client and vault_transit_key fixtures.
Marker: crypto
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.crypto

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Directories to exclude from scanning
EXCLUDED_DIRS = {".git", ".tck_cache", "__pycache__", "node_modules", ".venv", "venv"}

PRIVATE_KEY_INDICATORS = [
    "-----BEGIN PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----",
    "-----BEGIN EC PRIVATE KEY-----",
    "-----BEGIN OPENSSH PRIVATE KEY-----",
    "-----BEGIN DSA PRIVATE KEY-----",
]


def _is_excluded(path: Path) -> bool:
    """Return True if path is under an excluded directory."""
    parts = set(path.parts)
    return bool(parts & EXCLUDED_DIRS)


def _scan_for_pem_content(base: Path) -> list[str]:
    """Walk all files under base and return paths containing PEM private key headers."""
    violations: list[str] = []
    for f in base.rglob("*"):
        if _is_excluded(f):
            continue
        if not f.is_file():
            continue
        if f.stat().st_size > 10 * 1024 * 1024:  # Skip files > 10MB
            continue
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            for indicator in PRIVATE_KEY_INDICATORS:
                if indicator in content:
                    violations.append(f"{f.relative_to(REPO_ROOT)}: contains '{indicator}'")
                    break
        except (OSError, PermissionError):
            pass
    return violations


# ---------------------------------------------------------------------------
# Test 1: No .pem or .key files committed
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_no_pem_files_committed_to_repo() -> None:
    """No .pem or .key files may exist in the repository."""
    violations: list[str] = []

    for f in REPO_ROOT.rglob("*"):
        if _is_excluded(f):
            continue
        if not f.is_file():
            continue
        suffix = f.suffix.lower()
        if suffix in (".pem", ".key", ".p12", ".pfx"):
            violations.append(str(f.relative_to(REPO_ROOT)))

        # Also check for PEM headers in any file
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            for indicator in PRIVATE_KEY_INDICATORS:
                if indicator in content:
                    violations.append(
                        f"{f.relative_to(REPO_ROOT)} (contains private key header)"
                    )
                    break
        except (OSError, PermissionError):
            pass

    assert not violations, (
        f"Private key material found in repository ({len(violations)} file(s)):\n"
        + "\n".join(f"  {v}" for v in violations)
    )


# ---------------------------------------------------------------------------
# Test 2: No private key fields in schema examples
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_no_private_keys_in_schema_examples() -> None:
    """Schema examples must not contain private key fields or PEM material."""
    schemas_root = REPO_ROOT / "schemas"
    if not schemas_root.exists():
        pytest.skip("schemas/ not found")

    forbidden_field_names = {"privateKey", "private_key", "pkcs8", "p12", "pfx"}
    violations: list[str] = []

    for example_file in schemas_root.rglob("examples/**/*.json"):
        if _is_excluded(example_file):
            continue
        try:
            content = example_file.read_text(encoding="utf-8")
        except (OSError, PermissionError):
            continue

        for field_name in forbidden_field_names:
            if f'"{field_name}"' in content:
                violations.append(
                    f"{example_file.relative_to(REPO_ROOT)}: contains field '{field_name}'"
                )
        for indicator in PRIVATE_KEY_INDICATORS:
            if indicator in content:
                violations.append(
                    f"{example_file.relative_to(REPO_ROOT)}: contains PEM private key header"
                )

    assert not violations, (
        f"Private key material in schema examples ({len(violations)} file(s)):\n"
        + "\n".join(f"  {v}" for v in violations)
    )


# ---------------------------------------------------------------------------
# Test 3: No raw keys in test data
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_no_raw_keys_in_test_data() -> None:
    """tests/data/ must not contain private key material."""
    test_data_dir = REPO_ROOT / "tests" / "data"
    if not test_data_dir.exists():
        pytest.skip("tests/data/ not found")

    forbidden_field_names = {"privateKey", "private_key", "pkcs8"}
    violations: list[str] = []

    for data_file in test_data_dir.rglob("*"):
        if _is_excluded(data_file):
            continue
        if not data_file.is_file():
            continue
        try:
            content = data_file.read_text(encoding="utf-8", errors="replace")
        except (OSError, PermissionError):
            continue

        for indicator in PRIVATE_KEY_INDICATORS:
            if indicator in content:
                violations.append(
                    f"{data_file.relative_to(REPO_ROOT)}: contains PEM private key header"
                )
        for field_name in forbidden_field_names:
            if f'"{field_name}"' in content:
                violations.append(
                    f"{data_file.relative_to(REPO_ROOT)}: contains field '{field_name}'"
                )

    assert not violations, (
        f"Private key material in test data ({len(violations)} file(s)):\n"
        + "\n".join(f"  {v}" for v in violations)
    )


# ---------------------------------------------------------------------------
# Test 4: Vault Transit key export disabled
# ---------------------------------------------------------------------------


@pytest.mark.crypto
def test_vault_transit_key_export_disabled(vault_client, vault_transit_key) -> None:
    """
    A Vault Transit key created without exportable=True must not be exportable.

    Attempting to export it must return 403 or the key's exportable property must be False.
    """
    hvac = pytest.importorskip("hvac")

    # Check key metadata — exportable should be False
    key_detail = vault_client.secrets.transit.read_key(name=vault_transit_key)
    key_data = key_detail.get("data", key_detail)

    exportable = key_data.get("exportable", False)
    assert exportable is False, (
        f"Transit key '{vault_transit_key}' must not be exportable (exportable=True). "
        f"Got exportable={exportable!r}"
    )

    # Also attempt export and assert it fails
    try:
        export_result = vault_client.secrets.transit.export_key(
            name=vault_transit_key,
            key_type="signing-key",
        )
        # If we get here, the export succeeded — this is a security violation
        pytest.fail(
            f"Transit key '{vault_transit_key}' was exported successfully — "
            f"this is a key custody violation. Export must be disabled."
        )
    except Exception as exc:
        # Expected: 403 Forbidden or similar error
        assert any(
            indicator in str(exc).lower()
            for indicator in ["403", "forbidden", "not allowed", "exportable", "permission"]
        ), (
            f"Expected a permission/forbidden error when exporting non-exportable key. "
            f"Got: {exc}"
        )
