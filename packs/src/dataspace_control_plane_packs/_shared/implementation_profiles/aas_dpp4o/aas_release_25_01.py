"""AAS Release 25-01 metamodel constants and utilities.

Normative reference: IDTA AAS Specification Release 25-01.
Source pinned under vocab/pinned/ in each consuming pack.

This module carries no business logic — it is a typed vocabulary and
helper layer that packs import to ensure consistent AAS metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


# ---------------------------------------------------------------------------
# AAS metamodel vocabulary constants (AAS Part 1, Release 25-01)
# ---------------------------------------------------------------------------

AAS_RELEASE = "25-01"
AAS_SPEC_URI = "https://industrialdigitaltwin.io/aas-specifications"

# Model element kinds
KIND_INSTANCE = "Instance"
KIND_TEMPLATE = "Template"

# Submodel element categories
CATEGORY_PARAMETER = "PARAMETER"
CATEGORY_VARIABLE = "VARIABLE"
CATEGORY_CONSTANT = "CONSTANT"

# Identifier types (AAS Part 1 §5)
ID_IRI = "IRI"
ID_CUSTOM = "CUSTOM"

# Qualifier types
QUALIFIER_CONCEPT = "ConceptDescription"
QUALIFIER_TEMPLATE_QUALIFIER = "TemplateQualifier"

# Asset administration shell asset kinds
ASSET_KIND_INSTANCE = "Instance"
ASSET_KIND_TYPE = "Type"

# Submodel elements
SME_PROPERTY = "Property"
SME_MULTILANGUAGE = "MultiLanguageProperty"
SME_RANGE = "Range"
SME_BLOB = "Blob"
SME_FILE = "File"
SME_REFERENCE_ELEMENT = "ReferenceElement"
SME_SUBMODEL_ELEMENT_COLLECTION = "SubmodelElementCollection"
SME_SUBMODEL_ELEMENT_LIST = "SubmodelElementList"
SME_OPERATION = "Operation"
SME_EVENT_ELEMENT = "BasicEventElement"
SME_ANNOTATED_RELATIONSHIP = "AnnotatedRelationshipElement"
SME_RELATIONSHIP = "RelationshipElement"
SME_CAPABILITY = "Capability"
SME_ENTITY = "Entity"

# Value types
VT_STRING = "xs:string"
VT_INT = "xs:int"
VT_LONG = "xs:long"
VT_FLOAT = "xs:float"
VT_DOUBLE = "xs:double"
VT_BOOLEAN = "xs:boolean"
VT_DATE = "xs:date"
VT_DATETIME = "xs:dateTime"
VT_URI = "xs:anyURI"

# Security
ACCESS_PERMISSION_RULE = "AccessPermissionRule"
PERMISSION_KIND_ALLOW = "allow"
PERMISSION_KIND_DENY = "deny"
PERMISSION_KIND_NOT_APPLICABLE = "notApplicable"


@dataclass(frozen=True)
class AasId:
    """Typed AAS identifier."""

    value: str
    id_type: Literal["IRI", "CUSTOM"] = "IRI"

    def base64url(self) -> str:
        """Base64url-encode the IRI for use in AAS Part 2 API paths."""
        import base64
        return base64.urlsafe_b64encode(self.value.encode()).rstrip(b"=").decode()

    @classmethod
    def from_base64url(cls, encoded: str) -> "AasId":
        """Decode a base64url-encoded AAS ID from an AAS Part 2 API path."""
        import base64
        padding = 4 - len(encoded) % 4
        if padding != 4:
            encoded += "=" * padding
        return cls(value=base64.urlsafe_b64decode(encoded).decode())


@dataclass(frozen=True)
class SemanticId:
    """Reference to a concept description that gives a submodel element its meaning."""

    value: str
    """IRI of the concept description (e.g. IRDI or IRI from eClass, IEC CDD, IDTA)."""


def property_element(
    id_short: str,
    value_type: str,
    *,
    value: str | None = None,
    semantic_id: str | None = None,
    description: str | None = None,
    category: str = CATEGORY_PARAMETER,
) -> dict:
    """Build a minimal AAS Property submodel element dict."""
    el: dict = {
        "modelType": SME_PROPERTY,
        "idShort": id_short,
        "valueType": value_type,
        "category": category,
    }
    if value is not None:
        el["value"] = value
    if semantic_id:
        el["semanticId"] = {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": semantic_id}]}
    if description:
        el["description"] = [{"language": "en", "text": description}]
    return el


def submodel_element_collection(
    id_short: str,
    elements: list[dict],
    *,
    semantic_id: str | None = None,
    description: str | None = None,
) -> dict:
    """Build an AAS SubmodelElementCollection."""
    col: dict = {
        "modelType": SME_SUBMODEL_ELEMENT_COLLECTION,
        "idShort": id_short,
        "value": elements,
    }
    if semantic_id:
        col["semanticId"] = {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": semantic_id}]}
    if description:
        col["description"] = [{"language": "en", "text": description}]
    return col


def minimal_submodel(
    submodel_id: str,
    id_short: str,
    elements: list[dict],
    *,
    semantic_id: str | None = None,
    kind: str = KIND_INSTANCE,
) -> dict:
    """Build a minimal AAS Submodel envelope."""
    sm: dict = {
        "modelType": "Submodel",
        "id": submodel_id,
        "idShort": id_short,
        "kind": kind,
        "submodelElements": elements,
    }
    if semantic_id:
        sm["semanticId"] = {"type": "ExternalReference", "keys": [{"type": "GlobalReference", "value": semantic_id}]}
    return sm
