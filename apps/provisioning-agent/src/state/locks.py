"""
Lock manager: prevents concurrent apply runs against the same environment.
Currently uses a file-based lock (suitable for single-process / Kubernetes Job runs).
Will be replaced by Redis or etcd-backed distributed lock for HA reconcile loops.

Note: file_lock uses fcntl, which is POSIX-only and will NOT work on Windows.
"""
from __future__ import annotations
import fcntl
import os
import time
from contextlib import contextmanager
from pathlib import Path
import structlog

logger = structlog.get_logger(__name__)

DEFAULT_LOCK_DIR = Path(os.getenv("PROVISIONING_LOCK_DIR", "/tmp/provisioning-locks"))


@contextmanager
def file_lock(resource_name: str, lock_dir: Path = DEFAULT_LOCK_DIR, timeout: float = 60.0):
    """
    Acquire a per-resource file lock. Blocks up to `timeout` seconds.
    Use as a context manager around apply() calls to prevent concurrent runs.

    POSIX only: relies on fcntl.flock, which is not available on Windows.
    """
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"{resource_name}.lock"
    deadline = time.monotonic() + timeout
    lock_fd = open(lock_path, "w")
    try:
        acquired = False
        while time.monotonic() < deadline:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
                break
            except OSError:
                time.sleep(0.5)
        if not acquired:
            raise TimeoutError(
                f"Could not acquire lock for '{resource_name}' within {timeout}s. "
                "Is another apply running?"
            )
        logger.debug("lock.acquired", resource=resource_name)
        try:
            yield
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            logger.debug("lock.released", resource=resource_name)
    finally:
        lock_fd.close()
