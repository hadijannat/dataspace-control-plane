"""Public import surface for the AAS DPP4.0 shared implementation profile."""
from __future__ import annotations

from .access_model import AccessMatrix, AccessPermission, AccessSubject
from .aas_release_25_01 import (
    AAS_RELEASE,
    AasId,
    KIND_INSTANCE,
    KIND_TEMPLATE,
    SemanticId,
    minimal_submodel,
    property_element,
    submodel_element_collection,
)
from .id_link import IdLink, build_aas_id, build_id_link
from .submodel_catalog import STANDARD_SUBMODELS, SubmodelEntry, nameplate_template

__all__ = [
    "AAS_RELEASE",
    "AasId",
    "SemanticId",
    "KIND_INSTANCE",
    "KIND_TEMPLATE",
    "minimal_submodel",
    "property_element",
    "submodel_element_collection",
    "AccessMatrix",
    "AccessPermission",
    "AccessSubject",
    "IdLink",
    "build_aas_id",
    "build_id_link",
    "STANDARD_SUBMODELS",
    "SubmodelEntry",
    "nameplate_template",
]
