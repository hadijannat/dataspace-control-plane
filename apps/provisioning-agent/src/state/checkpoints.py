"""
Checkpoint manager: persists applied changes so reconcile is idempotent.
Simple JSON files per resource type — not a full state backend.
"""
import json
import pathlib
import structlog
from typing import Any

logger = structlog.get_logger(__name__)


class CheckpointManager:
    def __init__(self, checkpoint_dir: str) -> None:
        self._dir = pathlib.Path(checkpoint_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> pathlib.Path:
        return self._dir / f"{key.replace('/', '_')}.json"

    def load(self, key: str) -> dict[str, Any] | None:
        p = self._path(key)
        if not p.exists():
            return None
        return json.loads(p.read_text())

    def save(self, key: str, data: dict[str, Any]) -> None:
        self._path(key).write_text(json.dumps(data, indent=2))
        logger.debug("checkpoint.saved", key=key)

    def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            p.unlink()
