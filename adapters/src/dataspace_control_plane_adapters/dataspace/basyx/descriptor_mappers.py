"""BaSyx AAS descriptor mappers.

Translates between BaSyx AAS Registry wire-format descriptors and the
canonical TwinDescriptor structure from core/domains/twins/model/value_objects.py.

AAS Part 2 Shell Descriptor shape::

    {
        "id": "urn:...",
        "globalAssetId": "urn:...",
        "specificAssetIds": [...],
        "submodelDescriptors": [
            {
                "id": "urn:...",
                "semanticId": {"type": "ExternalReference", "keys": [...]},
                "endpoints": [{"interface": "SUBMODEL-3.0", "protocolInformation": {...}}]
            }
        ]
    }

AAS IDs must be base64URL-encoded (no padding) per AAS Part 2 API spec §3.2.
"""
from __future__ import annotations

import base64
from typing import Any


def encode_aas_id(aas_id: str) -> str:
    """Base64URL-encode an AAS ID per AAS Part 2 API spec §3.2.

    The AAS Part 2 REST API requires AAS IDs (and Submodel IDs) to be
    Base64URL-encoded (RFC 4648 §5) without padding when used in URL path
    segments to avoid ambiguity with URL-reserved characters.

    Args:
        aas_id: The raw AAS ID string (e.g. a URN or URL).

    Returns:
        Base64URL-encoded string without padding characters.
    """
    return base64.urlsafe_b64encode(aas_id.encode()).rstrip(b"=").decode("ascii")


def decode_aas_id(encoded: str) -> str:
    """Base64URL-decode an AAS ID from a URL path segment.

    Args:
        encoded: Base64URL-encoded AAS ID string (padding optional).

    Returns:
        Original AAS ID string.
    """
    # Restore padding
    pad = 4 - len(encoded) % 4
    if pad != 4:
        encoded += "=" * pad
    return base64.urlsafe_b64decode(encoded).decode()


def map_shell_descriptor_to_canonical(raw: dict[str, Any]) -> dict[str, Any]:
    """Translate a BaSyx AAS Shell Descriptor to a canonical twin dict.

    Output shape::

        {
            "twin_id": str,               # AAS ID (raw, not encoded)
            "global_asset_id": str,
            "specific_asset_ids": list[dict],
            "endpoints": list[dict],       # from submodel endpoint protocols
            "submodels": list[dict],       # normalized submodel descriptor entries
        }

    Args:
        raw: BaSyx AAS Registry shell descriptor dict.

    Returns:
        Canonical twin dict (plain dict, not a domain type).
    """
    submodel_descriptors: list[dict[str, Any]] = raw.get("submodelDescriptors") or []
    canonical_submodels = [_map_submodel_descriptor(sm) for sm in submodel_descriptors]

    # Collect all endpoint protocol information from all submodels.
    all_endpoints: list[dict[str, Any]] = []
    for sm in submodel_descriptors:
        for ep in sm.get("endpoints") or []:
            proto = ep.get("protocolInformation") or {}
            all_endpoints.append({
                "interface": ep.get("interface", ""),
                "href": proto.get("href") or proto.get("endpointAddress") or "",
                "subprotocol": proto.get("subprotocol") or None,
            })

    return {
        "twin_id": raw.get("id") or "",
        "global_asset_id": raw.get("globalAssetId") or "",
        "specific_asset_ids": raw.get("specificAssetIds") or [],
        "endpoints": all_endpoints,
        "submodels": canonical_submodels,
    }


def map_canonical_to_shell_descriptor(canonical: dict[str, Any]) -> dict[str, Any]:
    """Translate a canonical twin dict back to a BaSyx AAS Shell Descriptor.

    This is the inverse of map_shell_descriptor_to_canonical and is used
    when registering a twin in the BaSyx AAS Registry.

    Args:
        canonical: Canonical twin dict (from core TwinDescriptor fields).

    Returns:
        BaSyx AAS Registry shell descriptor dict ready for POST/PUT.
    """
    submodel_descriptors: list[dict[str, Any]] = []
    for sm in canonical.get("submodels") or []:
        sm_desc: dict[str, Any] = {
            "id": sm.get("id") or sm.get("submodel_id") or "",
        }
        semantic_id = sm.get("semantic_id")
        if semantic_id:
            sm_desc["semanticId"] = {
                "type": "ExternalReference",
                "keys": [{"type": "GlobalReference", "value": semantic_id}],
            }
        endpoint_url = sm.get("endpoint_url")
        if endpoint_url:
            sm_desc["endpoints"] = [
                {
                    "interface": sm.get("interface", "SUBMODEL-3.0"),
                    "protocolInformation": {
                        "href": endpoint_url,
                        "endpointProtocol": sm.get("endpoint_protocol", "HTTP"),
                    },
                }
            ]
        submodel_descriptors.append(sm_desc)

    descriptor: dict[str, Any] = {
        "id": canonical.get("twin_id") or canonical.get("id") or "",
        "globalAssetId": canonical.get("global_asset_id") or "",
    }
    if canonical.get("specific_asset_ids"):
        descriptor["specificAssetIds"] = canonical["specific_asset_ids"]
    if submodel_descriptors:
        descriptor["submodelDescriptors"] = submodel_descriptors
    return descriptor


def _map_submodel_descriptor(sm: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single submodel descriptor entry."""
    semantic_id_raw: dict[str, Any] = sm.get("semanticId") or {}
    keys: list[dict[str, Any]] = semantic_id_raw.get("keys") or []
    semantic_id_value = keys[0].get("value") if keys else None

    endpoints: list[dict[str, Any]] = sm.get("endpoints") or []
    first_endpoint = endpoints[0] if endpoints else {}
    proto = first_endpoint.get("protocolInformation") or {}

    return {
        "id": sm.get("id") or "",
        "semantic_id": semantic_id_value,
        "interface": first_endpoint.get("interface") or "SUBMODEL-3.0",
        "endpoint_url": proto.get("href") or proto.get("endpointAddress") or "",
        "endpoint_protocol": proto.get("endpointProtocol") or "HTTP",
    }
