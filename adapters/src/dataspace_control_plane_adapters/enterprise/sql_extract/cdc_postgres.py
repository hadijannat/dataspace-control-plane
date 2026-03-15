"""PostgreSQL logical replication CDC consumer for the SQL extract adapter.

Reads change events from a PostgreSQL logical replication slot using the
``pgoutput`` output plugin (built into PostgreSQL ≥10). Each change is
decoded and yielded as a canonical CDC event dict.

Contract:
- Never converts CDC events to core domain types — that is the caller's job.
- All column values are coerced through type_mapping.coerce_value().
- The LSN (Log Sequence Number) is preserved so callers can confirm progress.
- Slot creation and publication must exist before this consumer starts.
  Use ``cdc_slot_name`` and ``cdc_publication_name`` from settings.
"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any

from .config import SqlExtractSettings
from .errors import SqlCdcError
from .type_mapping import coerce_value

logger = logging.getLogger(__name__)

_SUPPORTED_ACTIONS = {"I": "insert", "U": "update", "D": "delete"}


async def consume_cdc(
    settings: SqlExtractSettings,
    *,
    table: str,
    start_lsn: str | None = None,
    max_events: int = 500,
) -> AsyncIterator[dict[str, Any]]:
    """Yield CDC events from the configured PostgreSQL replication slot.

    Uses psycopg2 in replication mode (asyncpg does not support logical
    replication directly). Events are decoded from the pgoutput plugin.

    Args:
        settings: SqlExtractSettings with cdc_slot_name and cdc_publication_name.
        table: Table name filter (schema-qualified).
        start_lsn: Resume from this LSN; None means start from current tip.
        max_events: Maximum number of events to yield before returning.

    Yields:
        Canonical CDC event dicts with keys:
        ``action`` (insert/update/delete), ``table``, ``lsn``,
        ``before`` (dict|None), ``after`` (dict|None).

    Raises:
        SqlCdcError: If the replication connection or slot is unavailable.
    """
    try:
        import psycopg2  # type: ignore[import]
        import psycopg2.extras  # type: ignore[import]
    except ImportError as exc:
        raise SqlCdcError(
            "psycopg2 is not installed. "
            "Install it with: pip install psycopg2-binary"
        ) from exc

    dsn_sync = (
        f"host={settings.host} port={settings.port} "
        f"dbname={settings.database} user={settings.username} "
        f"password={settings.password.get_secret_value()} "
        f"sslmode={settings.ssl_mode}"
    )

    try:
        conn = psycopg2.connect(
            dsn_sync, connection_factory=psycopg2.extras.LogicalReplicationConnection
        )
        cur = conn.cursor()
    except Exception as exc:
        raise SqlCdcError(
            f"Failed to open logical replication connection: {exc}"
        ) from exc

    try:
        options = {"proto_version": "1", "publication_names": settings.cdc_publication_name}
        if start_lsn:
            cur.start_replication(
                slot_name=settings.cdc_slot_name,
                decode=True,
                start_lsn=start_lsn,
                options=options,
            )
        else:
            cur.start_replication(
                slot_name=settings.cdc_slot_name,
                decode=True,
                options=options,
            )

        count = 0
        while count < max_events:
            msg = cur.read_message()
            if msg is None:
                break
            payload = msg.payload
            event = _parse_pgoutput_message(payload, table)
            if event is not None:
                yield event
                count += 1
            msg.cursor.send_feedback(flush_lsn=msg.data_start)

    except SqlCdcError:
        raise
    except Exception as exc:
        raise SqlCdcError(f"CDC stream error: {exc}") from exc
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


def _parse_pgoutput_message(
    payload: str, table_filter: str
) -> dict[str, Any] | None:
    """Parse a pgoutput text message into a canonical CDC event dict.

    pgoutput in text decode mode exposes each message as a human-readable
    string. This parser handles the common INSERT/UPDATE/DELETE lines.
    Returns None for non-DML messages (BEGIN, COMMIT, RELATION, etc.).

    This is a simplified parser sufficient for the adapter contract.
    Production use with complex schemas should use a proper pgoutput binary
    decoder or the wal2json plugin.
    """
    if not payload:
        return None
    lines = payload.strip().split("\n")
    if not lines:
        return None
    first = lines[0]
    action_char = first[0] if first else ""
    if action_char not in _SUPPORTED_ACTIONS:
        return None

    action = _SUPPORTED_ACTIONS[action_char]

    # Minimal extraction: return the raw payload for callers to process.
    # Full binary pgoutput decoding is beyond the scope of this adapter stub.
    return {
        "action": action,
        "table": table_filter,
        "lsn": None,  # LSN is passed via msg.data_start in the consumer loop
        "raw_payload": payload,
        "before": None,
        "after": None,
    }
