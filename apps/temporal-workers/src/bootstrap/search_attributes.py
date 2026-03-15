"""
Custom Search Attribute definitions for the Temporal namespace.

Derived from procedures._shared.search_attributes.ALL_SA_KEYS so that
attribute names and indexed types stay in sync with the procedures package.
Falls back to a hardcoded map if the procedures package is not installed.

Search attribute types:
  - "Keyword" — exact-match, used for IDs, enums, statuses
  - "Text"    — full-text search, used for free-form references

All attributes must be pre-registered in the Temporal namespace before
workers start. ensure_search_attributes() is idempotent and safe to call
on every startup.
"""
from __future__ import annotations

import structlog
from temporalio.client import Client
from temporalio.service import RPCError
from src.bootstrap.procedure_catalog import import_procedures_package

logger = structlog.get_logger(__name__)

# Known TEXT-indexed attribute names — everything else defaults to Keyword.
_TEXT_ATTR_NAMES: frozenset[str] = frozenset({"external_reference"})


def _derive_type(key: object) -> str:
    """Infer 'Keyword' or 'Text' from a temporalio SearchAttributeKey object.

    temporalio.common.SearchAttributeKey exposes an ``indexed_type`` property
    that returns ``SearchAttributeIndexedValueType.TEXT`` or ``KEYWORD``.
    If the attribute is absent (older SDK), fall back to name-based detection.
    """
    indexed_type = getattr(key, "indexed_type", None)
    if indexed_type is not None:
        return "Text" if "TEXT" in str(indexed_type).upper() else "Keyword"
    name: str = getattr(key, "name", "")
    return "Text" if name in _TEXT_ATTR_NAMES else "Keyword"


def _build_sa_type_map() -> dict[str, str]:
    """Build {attr_name: type_string} from procedures._shared.search_attributes.ALL_SA_KEYS.

    Falls back to a hardcoded, correctly-typed map when the procedures package
    is not yet installed in this environment.
    """
    try:
        import_procedures_package()
        from dataspace_control_plane_procedures._shared.search_attributes import (
            ALL_SA_KEYS,
        )
        return {key.name: _derive_type(key) for key in ALL_SA_KEYS}
    except ImportError:
        logger.warning(
            "search_attributes.procedures_not_installed",
            message=(
                "procedures package not found — using hardcoded SA map. "
                "Install dataspace-control-plane-procedures to derive types automatically."
            ),
        )
        return {
            "tenant_id": "Keyword",
            "legal_entity_id": "Keyword",
            "procedure_type": "Keyword",
            "external_reference": "Text",
            "agreement_id": "Keyword",
            "asset_id": "Keyword",
            "status": "Keyword",
            "pack_id": "Keyword",
        }


# Built once at module load; worker startup calls ensure_search_attributes() to register.
SEARCH_ATTRIBUTES: dict[str, str] = _build_sa_type_map()


async def ensure_search_attributes(client: Client) -> None:
    """Idempotently register custom search attributes in the Temporal namespace.

    Safe to call on every startup — existing attributes are left unchanged.
    """
    for name, attr_type in SEARCH_ATTRIBUTES.items():
        try:
            await client.operator_service.add_search_attributes(
                namespace=client.namespace,
                search_attributes={name: attr_type},  # type: ignore[arg-type]
            )
            logger.info("search_attribute.registered", name=name, type=attr_type)
        except RPCError as exc:
            if "already exists" in str(exc).lower():
                logger.debug("search_attribute.already_exists", name=name)
            else:
                logger.warning(
                    "search_attribute.registration_failed",
                    name=name,
                    error=str(exc),
                )
