"""DSP message → canonical dict mappers.

Converts validated DSP Pydantic message objects into plain Python dicts that
conform to the canonical shape expected by core/ domain services and procedures/.

Rules:
- Input: validated DSP Pydantic models from ``messages.py``.
- Output: plain Python dicts with snake_case keys — never domain aggregates.
- No I/O, no side effects. Pure transformation functions.
- Do not include JSON-LD internals (``@context``, ``@type``) in outputs.
"""
from __future__ import annotations

from typing import Any

from .messages import (
    DspCatalogResponse,
    DspContractAgreementMessage,
    DspNegotiationEventMessage,
    DspTransferRequestMessage,
)


def map_catalog_to_offers(response: DspCatalogResponse) -> list[dict[str, Any]]:
    """Convert a DSP catalog response to a list of canonical offer dicts.

    Each offer-dict represents a single ``odrl:hasPolicy`` entry found in a
    catalog dataset. Datasets without a policy are silently skipped.

    Canonical shape per offer::
        {
            "offer_id": str,       # ODRL offer @id
            "asset_id": str,       # dcat:Dataset @id (asset IRI)
            "policy_id": str,      # same as offer_id per DSP spec
            "provider": str | None,
            "provider_url": str | None,
        }

    Args:
        response: Validated ``DspCatalogResponse`` instance.

    Returns:
        Flat list of canonical offer dicts (may be empty if catalog has no offers).
    """
    results: list[dict[str, Any]] = []

    # Extract provider identity from dcat:service if present.
    provider: str | None = None
    provider_url: str | None = None
    service = response.service
    if isinstance(service, dict):
        provider = service.get("dspace:participantId") or service.get("dct:title")
        provider_url = service.get("dcat:endpointURL")
    elif isinstance(service, list) and service:
        first = service[0]
        provider = first.get("dspace:participantId") or first.get("dct:title")
        provider_url = first.get("dcat:endpointURL")

    for dataset in response.datasets:
        asset_id = dataset.get("@id", "")
        has_policy = dataset.get("odrl:hasPolicy")
        if has_policy is None:
            continue
        # DSP allows hasPolicy to be a single object or a list.
        if isinstance(has_policy, dict):
            policies = [has_policy]
        elif isinstance(has_policy, list):
            policies = has_policy
        else:
            continue

        for policy in policies:
            offer_id = policy.get("@id", "")
            results.append(
                {
                    "offer_id": offer_id,
                    "asset_id": asset_id,
                    "policy_id": offer_id,  # DSP: offer @id IS the policy reference
                    "provider": provider,
                    "provider_url": provider_url,
                }
            )

    return results


def map_agreement_to_record(
    msg: DspContractAgreementMessage,
) -> dict[str, Any]:
    """Convert a DSP ContractAgreementMessage to a canonical agreement record.

    Canonical shape::
        {
            "agreement_id": str,
            "policy_id": str,            # ODRL agreement @id
            "asset_id": str,             # odrl:target IRI
            "consumer_did": str | None,
            "provider_did": str | None,
            "timestamp": str | None,     # ISO-8601 string if present
        }

    Args:
        msg: Validated ``DspContractAgreementMessage``.

    Returns:
        Canonical agreement record dict.
    """
    agreement = msg.agreement
    agreement_id: str = agreement.get("@id", "")
    asset_id: str = agreement.get("odrl:target", "") or agreement.get("target", "")
    consumer_did: str | None = (
        agreement.get("dspace:consumer")
        or agreement.get("consumer")
    )
    provider_did: str | None = (
        agreement.get("dspace:provider")
        or agreement.get("provider")
    )
    timestamp: str | None = (
        agreement.get("dspace:timestamp")
        or agreement.get("timestamp")
    )

    return {
        "agreement_id": agreement_id,
        "policy_id": agreement_id,  # In DSP the agreement @id encodes the policy
        "asset_id": asset_id,
        "consumer_did": consumer_did,
        "provider_did": provider_did,
        "timestamp": timestamp,
    }


def map_transfer_request(msg: DspTransferRequestMessage) -> dict[str, Any]:
    """Convert a DSP TransferRequestMessage to a canonical transfer-request dict.

    Canonical shape::
        {
            "agreement_id": str,
            "format": str,
            "callback_url": str,
            "data_address": dict | None,
        }

    Args:
        msg: Validated ``DspTransferRequestMessage``.

    Returns:
        Canonical transfer request dict.
    """
    return {
        "agreement_id": msg.agreement_id,
        "format": msg.format,
        "callback_url": msg.callback_address,
        "data_address": dict(msg.data_address) if msg.data_address else None,
    }


def map_negotiation_event(msg: DspNegotiationEventMessage) -> dict[str, Any]:
    """Convert a DSP ContractNegotiationEventMessage to a canonical event dict.

    Canonical shape::
        {
            "provider_pid": str,
            "consumer_pid": str,
            "event_type": str,   # "dspace:FINALIZED" or "dspace:TERMINATED"
            "finalized": bool,
            "terminated": bool,
        }

    Args:
        msg: Validated ``DspNegotiationEventMessage``.

    Returns:
        Canonical negotiation event dict.
    """
    return {
        "provider_pid": msg.provider_pid,
        "consumer_pid": msg.consumer_pid,
        "event_type": msg.event_type,
        "finalized": msg.event_type == "dspace:FINALIZED",
        "terminated": msg.event_type == "dspace:TERMINATED",
    }
