"""Mappers from EDC wire models to canonical dicts.

Rules:
- Input: EdcXxxRaw Pydantic models (EDC wire format).
- Output: plain Python dicts — never domain aggregates or core/ types.
- No I/O, no side effects. Pure transformation functions only.
"""
from __future__ import annotations

from typing import Any

from .raw_models import (
    EdcAssetRaw,
    EdcCatalogRaw,
    EdcContractOfferRaw,
    EdcDatasetRaw,
    EdcNegotiationRaw,
)

# ---------------------------------------------------------------------------
# EDC negotiation state → internal status string
# ---------------------------------------------------------------------------

_EDC_STATE_MAP: dict[str, str] = {
    "INITIAL": "pending",
    "REQUESTING": "pending",
    "REQUESTED": "pending",
    "OFFERING": "pending",
    "OFFERED": "pending",
    "ACCEPTING": "pending",
    "ACCEPTED": "pending",
    "AGREEING": "pending",
    "AGREED": "agreed",
    "VERIFYING": "agreed",
    "VERIFIED": "agreed",
    "FINALIZING": "finalizing",
    "FINALIZED": "finalized",
    "TERMINATING": "terminating",
    "TERMINATED": "terminated",
}


def map_negotiation_state(raw: EdcNegotiationRaw) -> str:
    """Map an EDC negotiation state string to an internal status label.

    Returns ``"unknown"`` for states not present in the EDC SPI at build time.
    """
    return _EDC_STATE_MAP.get(raw.state.upper(), "unknown")


# ---------------------------------------------------------------------------
# Asset
# ---------------------------------------------------------------------------


def map_asset_to_ref(raw: EdcAssetRaw) -> dict[str, Any]:
    """Convert an EdcAssetRaw to a canonical asset-reference dict.

    Canonical shape::
        {
            "asset_id": str,
            "properties": dict,
            "data_address": dict | None,
        }
    """
    return {
        "asset_id": raw.id,
        "properties": dict(raw.properties),
        "data_address": dict(raw.data_address) if raw.data_address else None,
    }


# ---------------------------------------------------------------------------
# Catalog / offer snapshots
# ---------------------------------------------------------------------------


def _map_offer(offer: EdcContractOfferRaw, dataset_id: str) -> dict[str, Any]:
    """Map a single EdcContractOfferRaw to a canonical offer-snapshot dict."""
    return {
        "offer_id": offer.id,
        "asset_id": offer.asset_id or dataset_id,
        "policy": dict(offer.policy) if offer.policy else {},
    }


def _dataset_to_offer_snapshots(dataset: EdcDatasetRaw) -> list[dict[str, Any]]:
    """Extract all offer snapshots from a single catalog dataset entry."""
    if dataset.has_policy is None:
        return []
    if isinstance(dataset.has_policy, list):
        offers = dataset.has_policy
    else:
        offers = [dataset.has_policy]
    return [_map_offer(o, dataset.id) for o in offers]


def map_catalog_to_offer_snapshots(catalog_raw: EdcCatalogRaw) -> list[dict[str, Any]]:
    """Convert an EdcCatalogRaw to a flat list of canonical offer-snapshot dicts.

    Each element has the shape::
        {
            "offer_id": str,
            "asset_id": str,
            "policy": dict,
        }
    """
    results: list[dict[str, Any]] = []
    for dataset in catalog_raw.datasets:
        results.extend(_dataset_to_offer_snapshots(dataset))
    return results
