"""Checked-in generated BaSyx API clients.

These modules mirror the published BaSyx `/v3/api-docs` contracts while keeping
the hand-authored adapter surface stable in the parent package.
"""
from .aas_registry_api import GeneratedAasRegistryApi
from .submodel_registry_api import GeneratedSubmodelRegistryApi
from .submodel_repository_api import GeneratedSubmodelRepositoryApi

__all__ = [
    "GeneratedAasRegistryApi",
    "GeneratedSubmodelRegistryApi",
    "GeneratedSubmodelRepositoryApi",
]
