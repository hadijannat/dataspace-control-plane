"""Public import surface for the BaSyx adapter."""
from __future__ import annotations

from .aas_registry_client import AasRegistryClient
from .config import BasYxSettings
from .descriptor_mappers import (
    decode_aas_id,
    encode_aas_id,
    map_canonical_to_shell_descriptor,
    map_shell_descriptor_to_canonical,
)
from .errors import AasDescriptorNotFoundError, BasYxError, SubmodelNotFoundError
from .health import BasYxHealthProbe
from .ports_impl import BasYxAasRegistry, BasYxEndpointProbe
from .submodel_registry_client import SubmodelRegistryClient
from .submodel_repository_client import SubmodelRepositoryClient
from .value_only_mapper import extract_value_only, merge_value_only

__all__ = [
    "AasRegistryClient",
    "BasYxSettings",
    "BasYxAasRegistry",
    "BasYxEndpointProbe",
    "BasYxHealthProbe",
    "BasYxError",
    "AasDescriptorNotFoundError",
    "SubmodelNotFoundError",
    "SubmodelRegistryClient",
    "SubmodelRepositoryClient",
    "encode_aas_id",
    "decode_aas_id",
    "map_shell_descriptor_to_canonical",
    "map_canonical_to_shell_descriptor",
    "extract_value_only",
    "merge_value_only",
]
