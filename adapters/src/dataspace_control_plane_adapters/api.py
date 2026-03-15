"""Top-level import surface for the adapters package.

Each sub-group exposes its own api.py. This module re-exports the
adapter-factory functions used by apps/temporal-workers and apps/control-api
at container startup.

Usage pattern:
    from dataspace_control_plane_adapters.api import build_postgres_ports, build_edc_ports, ...
    ports = build_postgres_ports(cfg)

All concrete adapter wiring happens inside container/entrypoint code (apps/).
Never import adapters from core/ or procedures/.
"""
from __future__ import annotations

from importlib import import_module
from types import ModuleType
from typing import Final

_API_MODULES: Final[dict[str, str]] = {
    "edc": "dataspace_control_plane_adapters.dataspace.edc.api",
    "dsp": "dataspace_control_plane_adapters.dataspace.dsp.api",
    "dcp": "dataspace_control_plane_adapters.dataspace.dcp.api",
    "tractusx": "dataspace_control_plane_adapters.dataspace.tractusx.api",
    "gaiax": "dataspace_control_plane_adapters.dataspace.gaiax.api",
    "basyx": "dataspace_control_plane_adapters.dataspace.basyx.api",
    "sap_odata": "dataspace_control_plane_adapters.enterprise.sap_odata.api",
    "siemens_teamcenter": "dataspace_control_plane_adapters.enterprise.siemens_teamcenter.api",
    "kafka_ingest": "dataspace_control_plane_adapters.enterprise.kafka_ingest.api",
    "object_storage": "dataspace_control_plane_adapters.enterprise.object_storage.api",
    "sql_extract": "dataspace_control_plane_adapters.enterprise.sql_extract.api",
    "keycloak": "dataspace_control_plane_adapters.infrastructure.keycloak.api",
    "vault_kms": "dataspace_control_plane_adapters.infrastructure.vault_kms.api",
    "temporal_client": "dataspace_control_plane_adapters.infrastructure.temporal_client.api",
    "postgres": "dataspace_control_plane_adapters.infrastructure.postgres.api",
    "telemetry": "dataspace_control_plane_adapters.infrastructure.telemetry.api",
}

_LAZY_EXPORTS: Final[dict[str, tuple[str, str]]] = {
    "create_temporal_client": (
        "dataspace_control_plane_adapters.infrastructure.temporal_client.api",
        "create_temporal_client",
    ),
    "make_postgres_ports": (
        "dataspace_control_plane_adapters.infrastructure.postgres.api",
        "make_postgres_ports",
    ),
    "make_vault_ports": (
        "dataspace_control_plane_adapters.infrastructure.vault_kms.api",
        "make_vault_ports",
    ),
    "make_telemetry_ports": (
        "dataspace_control_plane_adapters.infrastructure.telemetry.api",
        "make_telemetry_ports",
    ),
}


def _load_api(name: str) -> ModuleType:
    try:
        module_path = _API_MODULES[name]
    except KeyError as exc:
        raise AttributeError(f"Unknown adapter api {name!r}") from exc
    return import_module(module_path)


def load_edc_api() -> ModuleType:
    return _load_api("edc")


def load_dsp_api() -> ModuleType:
    return _load_api("dsp")


def load_dcp_api() -> ModuleType:
    return _load_api("dcp")


def load_tractusx_api() -> ModuleType:
    return _load_api("tractusx")


def load_gaiax_api() -> ModuleType:
    return _load_api("gaiax")


def load_basyx_api() -> ModuleType:
    return _load_api("basyx")


def load_sap_odata_api() -> ModuleType:
    return _load_api("sap_odata")


def load_siemens_teamcenter_api() -> ModuleType:
    return _load_api("siemens_teamcenter")


def load_kafka_ingest_api() -> ModuleType:
    return _load_api("kafka_ingest")


def load_object_storage_api() -> ModuleType:
    return _load_api("object_storage")


def load_sql_extract_api() -> ModuleType:
    return _load_api("sql_extract")


def load_keycloak_api() -> ModuleType:
    return _load_api("keycloak")


def load_vault_kms_api() -> ModuleType:
    return _load_api("vault_kms")


def load_temporal_client_api() -> ModuleType:
    return _load_api("temporal_client")


def load_postgres_api() -> ModuleType:
    return _load_api("postgres")


def load_telemetry_api() -> ModuleType:
    return _load_api("telemetry")


def __getattr__(name: str) -> object:
    if name in _LAZY_EXPORTS:
        module_path, attr_name = _LAZY_EXPORTS[name]
        return getattr(import_module(module_path), attr_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "load_edc_api",
    "load_dsp_api",
    "load_dcp_api",
    "load_tractusx_api",
    "load_gaiax_api",
    "load_basyx_api",
    "load_sap_odata_api",
    "load_siemens_teamcenter_api",
    "load_kafka_ingest_api",
    "load_object_storage_api",
    "load_sql_extract_api",
    "load_keycloak_api",
    "load_vault_kms_api",
    "load_temporal_client_api",
    "load_postgres_api",
    "load_telemetry_api",
    "create_temporal_client",
    "make_postgres_ports",
    "make_vault_ports",
    "make_telemetry_ports",
]
