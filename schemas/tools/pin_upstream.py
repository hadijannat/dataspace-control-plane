#!/usr/bin/env python3
"""
schemas/tools/pin_upstream.py
Refresh vendored upstream artifacts and update schemas/locks/upstream.lock.yaml.

Usage:
    python schemas/tools/pin_upstream.py [--dry-run] [--family FAMILY] [--artifact ARTIFACT_ID]
"""
from __future__ import annotations

import argparse
import sys
import urllib.request
from datetime import datetime, timezone

from _support import SCHEMAS_ROOT, dump_yaml, load_yaml, sha256_bytes, sha256_file

LOCK_FILE = SCHEMAS_ROOT / "locks" / "upstream.lock.yaml"


def _download(entry: dict) -> tuple[bytes, str]:
    headers = {"User-Agent": "dataspace-control-plane-schema-pinner/1.0"}
    headers.update(entry.get("request_headers", {}))
    request = urllib.request.Request(entry["source_uri"], headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(), response.geturl()


def _load_lock() -> dict:
    return load_yaml(LOCK_FILE)


def _save_lock(lock: dict) -> None:
    dump_yaml(LOCK_FILE, lock)


def _matches_filters(entry: dict, family: str | None, artifact: str | None) -> bool:
    if family and entry.get("family") != family:
        return False
    if artifact and entry.get("artifact_id") != artifact:
        return False
    return True


def _verify_entry(entry: dict) -> tuple[bool, str]:
    local_path = SCHEMAS_ROOT / entry["local_path"]
    if not local_path.exists():
        return False, f"FAIL {entry['artifact_id']}: missing local file {entry['local_path']}"
    if entry.get("sha256") in (None, "PENDING") or entry.get("retrieved_at") in (None, "PENDING"):
        return False, f"FAIL {entry['artifact_id']}: unresolved lock metadata"
    actual = sha256_file(local_path)
    if actual != entry["sha256"]:
        return False, f"FAIL {entry['artifact_id']}: checksum mismatch expected {entry['sha256']} got {actual}"
    return True, f"OK   {entry['artifact_id']}: checksum verified"


def _pin_entry(entry: dict) -> tuple[bool, str]:
    try:
        payload, resolved_url = _download(entry)
    except Exception as exc:  # noqa: BLE001
        return False, f"FAIL {entry['artifact_id']}: download failed — {exc}"

    local_path = SCHEMAS_ROOT / entry["local_path"]
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(payload)
    entry["sha256"] = sha256_bytes(payload)
    entry["retrieved_at"] = datetime.now(tz=timezone.utc).isoformat()
    if resolved_url != entry["source_uri"]:
        entry["resolved_uri"] = resolved_url
    return True, f"DONE {entry['artifact_id']}: {entry['sha256']}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Verify vendored artifacts without fetching.")
    parser.add_argument("--family", help="Limit to one schema family.")
    parser.add_argument("--artifact", help="Limit to one artifact_id.")
    args = parser.parse_args(argv)

    lock = _load_lock()
    entries = [entry for entry in lock.get("upstream", []) if _matches_filters(entry, args.family, args.artifact)]
    if not entries:
        print("No matching entries in upstream.lock.yaml.")
        return 0

    failures = 0
    for entry in entries:
        ok, message = _verify_entry(entry) if args.dry_run else _pin_entry(entry)
        print(message)
        if not ok:
            failures += 1

    if not args.dry_run:
        lock["generated_at"] = datetime.now(tz=timezone.utc).date().isoformat()
        _save_lock(lock)

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
