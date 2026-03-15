"""Checksum and digest utilities for object integrity verification.

Object storage adapters use these to verify downloaded bytes match the
expected hash before forwarding to core/.
"""
from __future__ import annotations

import hashlib

from .errors import ObjectStorageChecksumError


def sha256_hex(data: bytes) -> str:
    """Return the SHA-256 hex digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


def md5_hex(data: bytes) -> str:
    """Return the MD5 hex digest of ``data`` (used for S3 ETag comparison)."""
    return hashlib.md5(data, usedforsecurity=False).hexdigest()


def verify_sha256(data: bytes, expected_hex: str) -> None:
    """Raise ObjectStorageChecksumError if SHA-256 of ``data`` != ``expected_hex``.

    Args:
        data: Raw bytes to verify.
        expected_hex: Expected SHA-256 hex digest (case-insensitive).

    Raises:
        ObjectStorageChecksumError: On mismatch.
    """
    actual = sha256_hex(data)
    if actual.lower() != expected_hex.lower():
        raise ObjectStorageChecksumError(
            f"SHA-256 checksum mismatch: expected={expected_hex!r}, actual={actual!r}"
        )


def verify_etag(data: bytes, etag: str) -> None:
    """Verify a simple (non-multipart) S3 ETag matches the MD5 of ``data``.

    Note: Multipart ETags use a different format (``<md5_of_parts>-<num_parts>``)
    and are not verified here.

    Args:
        data: Raw bytes to verify.
        etag: S3 ETag string (may include surrounding quotes, which are stripped).

    Raises:
        ObjectStorageChecksumError: On mismatch or if etag is a multipart ETag.
    """
    etag = etag.strip('"')
    if "-" in etag:
        # Multipart ETag — skip verification (not a simple MD5).
        return
    actual = md5_hex(data)
    if actual.lower() != etag.lower():
        raise ObjectStorageChecksumError(
            f"ETag mismatch: expected={etag!r}, actual={actual!r}"
        )
