"""Mappers for EDC webhook / callback event payloads.

EDC delivers asynchronous events to registered callback URLs via HTTP POST.
Each event is a JSON-LD document with an ``eventType`` field identifying the
transition that occurred.

Common event types (EDC 0.7+):
- ``contract.negotiation.finalized``  — negotiation reached FINALIZED state
- ``contract.negotiation.terminated`` — negotiation reached TERMINATED state
- ``transfer.process.started``        — transfer data flow is live
- ``transfer.process.completed``      — transfer completed successfully
- ``transfer.process.terminated``     — transfer reached TERMINATED state

Rules:
- Pure functions, no I/O.
- Raise ``EdcWebhookParseError`` on missing required fields.
- Return canonical plain dicts; never domain aggregates.
"""
from __future__ import annotations

from typing import Any

from .errors import EdcWebhookParseError


def _require(raw: dict[str, Any], *keys: str) -> None:
    """Assert that all ``keys`` are present in ``raw``, raise on missing."""
    missing = [k for k in keys if k not in raw]
    if missing:
        raise EdcWebhookParseError(
            f"EDC webhook payload missing required fields: {missing}. "
            f"Received keys: {list(raw.keys())}"
        )


def map_negotiation_event(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize an EDC contract-negotiation callback payload.

    Expected incoming shape (EDC callback)::
        {
            "id": "<negotiation-id>",
            "eventType": "contract.negotiation.finalized",
            "payload": {
                "contractNegotiationId": "<negotiation-id>",
                "contractAgreementId": "<agreement-id>",   # present on FINALIZED
                "state": "FINALIZED",
                ...
            }
        }

    Returns a canonical dict::
        {
            "event_type": str,          # e.g. "contract.negotiation.finalized"
            "negotiation_id": str,
            "state": str,               # EDC raw state string
            "agreement_id": str | None, # only set when FINALIZED
        }

    Raises:
        EdcWebhookParseError: If required fields are absent.
    """
    _require(raw, "eventType")
    payload = raw.get("payload", raw)

    negotiation_id = (
        payload.get("contractNegotiationId")
        or raw.get("id")
        or raw.get("@id")
    )
    if not negotiation_id:
        raise EdcWebhookParseError(
            "EDC negotiation event missing 'contractNegotiationId' / 'id'"
        )

    return {
        "event_type": raw["eventType"],
        "negotiation_id": negotiation_id,
        "state": payload.get("state", "UNKNOWN"),
        "agreement_id": payload.get("contractAgreementId"),
    }


def map_transfer_event(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize an EDC transfer-process callback payload.

    Expected incoming shape::
        {
            "id": "<transfer-id>",
            "eventType": "transfer.process.started",
            "payload": {
                "transferProcessId": "<transfer-id>",
                "state": "STARTED",
                ...
            }
        }

    Returns a canonical dict::
        {
            "event_type": str,       # e.g. "transfer.process.started"
            "transfer_id": str,
            "state": str,            # EDC raw state string
        }

    Raises:
        EdcWebhookParseError: If required fields are absent.
    """
    _require(raw, "eventType")
    payload = raw.get("payload", raw)

    transfer_id = (
        payload.get("transferProcessId")
        or raw.get("id")
        or raw.get("@id")
    )
    if not transfer_id:
        raise EdcWebhookParseError(
            "EDC transfer event missing 'transferProcessId' / 'id'"
        )

    return {
        "event_type": raw["eventType"],
        "transfer_id": transfer_id,
        "state": payload.get("state", "UNKNOWN"),
    }


def extract_agreement_id(negotiation_finalized_event: dict[str, Any]) -> str:
    """Extract the contract agreement ID from a finalized negotiation event.

    Args:
        negotiation_finalized_event: The *canonical* dict returned by
            :func:`map_negotiation_event` for a FINALIZED negotiation.

    Returns:
        The contract agreement ID string.

    Raises:
        EdcWebhookParseError: If the event does not carry an agreement ID
            (i.e. the negotiation was not in FINALIZED state).
    """
    agreement_id = negotiation_finalized_event.get("agreement_id")
    if not agreement_id:
        raise EdcWebhookParseError(
            "Cannot extract agreement_id: negotiation event has no 'agreement_id'. "
            "Ensure the negotiation reached FINALIZED state before calling this."
        )
    return agreement_id
