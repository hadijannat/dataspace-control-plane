#!/usr/bin/env python3
"""
schemas/tools/pin_upstream.py
Download / refresh pinned upstream artifacts and update upstream.lock.yaml.

Usage:
    python schemas/tools/pin_upstream.py [--dry-run] [--family FAMILY] [--artifact ARTIFACT_ID]

Flags:
    --dry-run     Verify checksums only; do not write files.
    --family      Limit to one schema family (e.g. vc, aas).
    --artifact    Limit to one artifact_id (e.g. w3c.vc-context-v2).

Exit codes:
    0  All artifacts present and checksums match (or dry-run succeeded).
    1  At least one artifact is missing or checksum mismatch.
    2  Usage error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import yaml  # type: ignore
except ImportError:
    print("ERROR: pyyaml is required.  Run: pip install pyyaml", file=sys.stderr)
    sys.exit(2)

SCHEMAS_ROOT = Path(__file__).resolve().parent.parent
LOCK_FILE = SCHEMAS_ROOT / "locks" / "upstream.lock.yaml"


@dataclass
class LockEntry:
    artifact_id: str
    family: str
    local_path: str
    source_uri: str
    standard: str
    version: str
    format: str
    retrieved_at: str
    sha256: str
    license: str
    notes: str = ""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _download(uri: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(uri, headers={"User-Agent": "dataspace-schema-pinner/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _load_lock() -> dict:
    if not LOCK_FILE.exists():
        return {"lock_version": "1.0.0", "upstream": []}
    with open(LOCK_FILE) as f:
        return yaml.safe_load(f)


def _save_lock(data: dict) -> None:
    LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK_FILE, "w") as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)


def pin_artifact(entry: dict, *, dry_run: bool = False) -> tuple[bool, str]:
    """Download and pin one artifact. Returns (success, message)."""
    local_path = SCHEMAS_ROOT / entry["local_path"]
    source_uri = entry["source_uri"]

    if entry.get("sha256", "PENDING") != "PENDING" and local_path.exists():
        # Verify existing file
        actual = _sha256(local_path.read_bytes())
        if actual == entry["sha256"]:
            return True, f"  OK  {entry['artifact_id']} (checksum verified)"
        return False, f"  FAIL {entry['artifact_id']}: checksum mismatch\n    expected {entry['sha256']}\n    got      {actual}"

    if dry_run:
        status = "PENDING" if entry.get("sha256", "PENDING") == "PENDING" else "missing"
        return False, f"  SKIP {entry['artifact_id']}: {status} (dry-run, no fetch)"

    print(f"  Fetching {source_uri} ...", file=sys.stderr)
    try:
        data = _download(source_uri)
    except Exception as exc:
        return False, f"  FAIL {entry['artifact_id']}: download failed — {exc}"

    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(data)
    digest = _sha256(data)
    entry["sha256"] = digest
    entry["retrieved_at"] = datetime.now(tz=timezone.utc).isoformat()
    return True, f"  DONE {entry['artifact_id']}: {digest}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Verify only, no downloads.")
    parser.add_argument("--family", help="Limit to one schema family.")
    parser.add_argument("--artifact", help="Limit to one artifact_id.")
    args = parser.parse_args(argv)

    lock = _load_lock()
    entries: list[dict] = lock.get("upstream", [])

    if args.family:
        entries = [e for e in entries if e.get("family") == args.family]
    if args.artifact:
        entries = [e for e in entries if e.get("artifact_id") == args.artifact]

    if not entries:
        print("No matching entries in upstream.lock.yaml.", file=sys.stderr)
        return 0

    failures = 0
    for entry in entries:
        ok, msg = pin_artifact(entry, dry_run=args.dry_run)
        print(msg)
        if not ok:
            failures += 1

    if not args.dry_run:
        _save_lock(lock)
        print(f"\nLock file updated: {LOCK_FILE}", file=sys.stderr)

    if failures:
        print(f"\n{failures} artifact(s) failed.", file=sys.stderr)
        return 1

    print("\nAll artifacts OK.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
