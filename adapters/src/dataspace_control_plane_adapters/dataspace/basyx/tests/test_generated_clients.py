from __future__ import annotations

import pytest

from dataspace_control_plane_adapters._shared.health import HealthStatus
from dataspace_control_plane_adapters.dataspace.basyx import api as basyx_api
from dataspace_control_plane_adapters.dataspace.basyx.aas_registry_client import (
    AasRegistryClient,
)
from dataspace_control_plane_adapters.dataspace.basyx.config import BasYxSettings
from dataspace_control_plane_adapters.dataspace.basyx.generated import (
    GeneratedAasRegistryApi,
    GeneratedSubmodelRegistryApi,
    GeneratedSubmodelRepositoryApi,
)
from dataspace_control_plane_adapters.dataspace.basyx.health import BasYxHealthProbe
from dataspace_control_plane_adapters.dataspace.basyx import aas_registry_client as aas_client_module


def _settings() -> BasYxSettings:
    return BasYxSettings(
        aas_registry_url="https://aas.example.com",
        submodel_registry_url="https://submodel-registry.example.com",
        submodel_repository_url="https://submodel-repository.example.com",
    )


class _FakeGeneratedAasRegistryApi:
    def __init__(self, _cfg: BasYxSettings) -> None:
        self.posted: list[dict[str, object]] = []

    async def __aenter__(self) -> "_FakeGeneratedAasRegistryApi":
        return self

    async def __aexit__(self, *_args) -> None:
        return None

    async def get_all_shell_descriptors(self) -> list[dict[str, object]]:
        return [{"id": "shell-1"}]

    async def post_shell_descriptor(self, descriptor: dict[str, object]) -> dict[str, object]:
        self.posted.append(descriptor)
        return descriptor


def test_public_api_hides_descriptor_mapper_helpers() -> None:
    leaked_symbols = {
        "encode_aas_id",
        "map_shell_descriptor_to_canonical",
        "extract_value_only",
    }

    assert leaked_symbols.isdisjoint(basyx_api.__all__)


@pytest.mark.asyncio
async def test_wrapper_client_delegates_to_checked_in_generated_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        aas_client_module,
        "GeneratedAasRegistryApi",
        _FakeGeneratedAasRegistryApi,
    )

    client = AasRegistryClient(_settings())

    assert await client.get_all_shell_descriptors() == [{"id": "shell-1"}]
    assert await client.post_shell_descriptor({"id": "shell-2"}) == {"id": "shell-2"}


def test_generated_modules_are_part_of_checked_in_adapter_surface() -> None:
    assert GeneratedAasRegistryApi is not None
    assert GeneratedSubmodelRegistryApi is not None
    assert GeneratedSubmodelRepositoryApi is not None


@pytest.mark.asyncio
async def test_basyx_health_probe_exposes_service_capabilities() -> None:
    probe = BasYxHealthProbe(_settings())

    descriptor = probe.capability_descriptor()

    assert "aas-registry" in descriptor["capabilities"]
    assert descriptor["adapter"] == "basyx"
