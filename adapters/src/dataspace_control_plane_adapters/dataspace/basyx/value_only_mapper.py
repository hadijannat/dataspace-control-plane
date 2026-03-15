"""AAS ValueOnly representation mapper.

The AAS Part 2 specification defines a ValueOnly JSON projection that
represents submodel element values as a flat JSON object. This module
provides utilities to extract and merge ValueOnly representations
from and back into structured Submodel dicts.

ValueOnly projection rules (AAS Part 2 §9.9):
- Property → "{idShort}": <value>
- SubmodelElementCollection → "{idShort}": { nested ValueOnly }
- File → "{idShort}": "<path>"
- Blob → omitted (binary, not in ValueOnly)
- ReferenceElement → "{idShort}": { reference dict }
- MultiLanguageProperty → "{idShort}": [{"language": str, "text": str}]

This mapper handles the common cases. Extended element types may require
pack-specific handling (see packs/).
"""
from __future__ import annotations

from typing import Any


def extract_value_only(submodel: dict[str, Any]) -> dict[str, Any]:
    """Extract a ValueOnly projection from a structured AAS v3 Submodel dict.

    Walks the ``submodelElements`` list and builds the flat ValueOnly dict
    per the AAS Part 2 §9.9 projection rules.

    Args:
        submodel: Full AAS v3 Submodel dict with ``submodelElements`` list.

    Returns:
        Flat ValueOnly dict. Nested collections become nested dicts.
    """
    elements: list[dict[str, Any]] = submodel.get("submodelElements") or []
    return _project_elements(elements)


def merge_value_only(submodel: dict[str, Any], values: dict[str, Any]) -> dict[str, Any]:
    """Merge updated ValueOnly values back into a structured Submodel dict.

    Walks the ``submodelElements`` list and updates element values in-place
    (returns a new dict, does not mutate the input).

    Args:
        submodel: Full AAS v3 Submodel dict (template structure).
        values: ValueOnly dict with updated values keyed by idShort.

    Returns:
        New Submodel dict with updated element values.
    """
    import copy
    updated = copy.deepcopy(submodel)
    elements: list[dict[str, Any]] = updated.get("submodelElements") or []
    _apply_values(elements, values)
    updated["submodelElements"] = elements
    return updated


def _project_elements(elements: list[dict[str, Any]]) -> dict[str, Any]:
    """Recursively project a list of submodel elements into ValueOnly format."""
    result: dict[str, Any] = {}
    for elem in elements:
        id_short = elem.get("idShort") or elem.get("id_short") or ""
        model_type = (elem.get("modelType") or "").lower()

        if model_type in ("submodelelementcollection", "submodelelementlist"):
            nested = elem.get("value") or []
            if isinstance(nested, list):
                result[id_short] = _project_elements(nested)
            else:
                result[id_short] = nested

        elif model_type == "multilanguageproperty":
            langs: list[dict[str, Any]] = elem.get("value") or []
            result[id_short] = langs  # list of {"language": str, "text": str}

        elif model_type == "referenceelement":
            ref = elem.get("value")
            result[id_short] = ref  # reference dict or None

        elif model_type == "file":
            result[id_short] = elem.get("value") or ""

        elif model_type == "blob":
            # Blobs are excluded from ValueOnly per AAS spec.
            pass

        else:
            # Property, Range, AnnotatedRelationshipElement, etc.
            result[id_short] = elem.get("value")

    return result


def _apply_values(
    elements: list[dict[str, Any]], values: dict[str, Any]
) -> None:
    """Recursively apply ValueOnly values into a list of element dicts (in-place)."""
    for elem in elements:
        id_short = elem.get("idShort") or elem.get("id_short") or ""
        if id_short not in values:
            continue

        model_type = (elem.get("modelType") or "").lower()
        new_value = values[id_short]

        if model_type in ("submodelelementcollection", "submodelelementlist"):
            nested: list[dict[str, Any]] = elem.get("value") or []
            if isinstance(new_value, dict) and isinstance(nested, list):
                _apply_values(nested, new_value)
                elem["value"] = nested
            else:
                elem["value"] = new_value
        elif model_type == "blob":
            # Blobs are read-only via ValueOnly; skip silently.
            pass
        else:
            elem["value"] = new_value
