#!/usr/bin/env python3
"""
schemas/tools/pin_upstream.py
Refresh vendored upstream artifacts and update schemas/locks/upstream.lock.yaml.

Usage:
    python schemas/tools/pin_upstream.py [--dry-run] [--family FAMILY] [--artifact ARTIFACT_ID]
"""
from __future__ import annotations

import argparse
import ipaddress
import socket
import sys
import urllib.request
from datetime import datetime, timezone
from urllib.parse import urlparse

from _support import SCHEMAS_ROOT, dump_yaml, load_yaml, sha256_bytes, sha256_file

LOCK_FILE = SCHEMAS_ROOT / "locks" / "upstream.lock.yaml"

# Only HTTPS is permitted for upstream fetches.
_ALLOWED_SCHEMES = frozenset({"https"})

# Private, loopback, and link-local ranges that must never be fetched (SSRF guard).
_PRIVATE_NETS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _validate_url(uri: str) -> None:
    """Raise ValueError for non-HTTPS schemes and private/loopback hosts (SSRF guard)."""
    parsed = urlparse(uri)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        raise ValueError(
            f"Refused to fetch '{uri}': only https:// is permitted "
            f"(got scheme '{parsed.scheme}')"
        )
    hostname = (parsed.hostname or "").lower()
    if not hostname or hostname == "localhost":
        raise ValueError(f"Refused to fetch '{uri}': empty or localhost host is not permitted")
    # Check if hostname is a literal IP address.
    try:
        addr = ipaddress.ip_address(hostname)
        for net in _PRIVATE_NETS:
            if addr in net:
                raise ValueError(
                    f"Refused to fetch '{uri}': host {hostname} is in a private/reserved range"
                )
    except ValueError as exc:
        if "private" in str(exc) or "reserved" in str(exc) or "loopback" in str(exc):
            raise
        # hostname is a DNS name — resolve all addresses and check each.
        try:
            for _family, _type, _proto, _canon, sockaddr in socket.getaddrinfo(
                hostname, None, proto=socket.IPPROTO_TCP
            ):
                addr = ipaddress.ip_address(sockaddr[0])
                for net in _PRIVATE_NETS:
                    if addr in net:
                        raise ValueError(
                            f"Refused to fetch '{uri}': resolved host "
                            f"{hostname} -> {addr} is private/reserved"
                        )
        except OSError:
            pass  # DNS failure; urlopen will also fail — let it propagate naturally.


def _validate_local_path(entry: dict) -> None:
    """Raise ValueError if entry['local_path'] escapes SCHEMAS_ROOT (path traversal guard)."""
    local_path = (SCHEMAS_ROOT / entry["local_path"]).resolve()
    try:
        local_path.relative_to(SCHEMAS_ROOT.resolve())
    except ValueError:
        raise ValueError(
            f"local_path for '{entry.get('artifact_id', '?')}' escapes SCHEMAS_ROOT: "
            f"{entry['local_path']}"
        )


def _download(entry: dict) -> tuple[bytes, str]:
    # SECURITY: validate URL scheme and host before any network access.
    _validate_url(entry["source_uri"])
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
    # SECURITY: reject path traversal before any file access.
    try:
        _validate_local_path(entry)
    except ValueError as exc:
        return False, f"FAIL {entry.get('artifact_id', '?')}: {exc}"

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
    # SECURITY: validate local_path containment before downloading anything.
    try:
        _validate_local_path(entry)
    except ValueError as exc:
        return False, f"FAIL {entry.get('artifact_id', '?')}: {exc}"

    try:
        payload, resolved_url = _download(entry)
    except Exception as exc:  # noqa: BLE001
        return False, f"FAIL {entry['artifact_id']}: download failed — {exc}"

    # SECURITY: compute checksum BEFORE writing to disk.
    actual_sha = sha256_bytes(payload)

    # SECURITY: if a pinned hash already exists (re-pin), reject mismatches.
    existing_sha = entry.get("sha256")
    if existing_sha and existing_sha not in (None, "PENDING") and actual_sha != existing_sha:
        return False, (
            f"FAIL {entry['artifact_id']}: downloaded payload checksum {actual_sha} "
            f"does not match existing pin {existing_sha} — refusing to overwrite"
        )

    local_path = SCHEMAS_ROOT / entry["local_path"]
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_bytes(payload)
    entry["sha256"] = actual_sha
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
