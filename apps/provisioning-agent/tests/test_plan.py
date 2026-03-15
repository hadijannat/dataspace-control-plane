from pathlib import Path

import pytest

from src.commands.plan import compute_state_diff, discover_actual_state, load_desired_state, _resource_is_present_via_control_api
from src.models.actual_state import ActualState, KeycloakRealmActual
from src.models.desired_state import DesiredState, KeycloakClientSpec, KeycloakRealmSpec


def test_load_desired_state_from_yaml(tmp_path: Path):
    manifest = tmp_path / "bootstrap.yaml"
    manifest.write_text(
        """
keycloak_realms:
  - realm: dataspace
    display_name: Dataspace
    clients:
      - client_id: web-console
        name: Web Console
        public_client: true
worker_namespaces:
  - onboarding
"""
    )

    desired = load_desired_state(str(tmp_path))

    assert desired.keycloak_realms[0].realm == "dataspace"
    assert desired.keycloak_realms[0].clients[0].client_id == "web-console"
    assert desired.worker_namespaces == ["onboarding"]


def test_compute_state_diff_detects_missing_realm_and_client(tmp_path: Path):
    desired = load_desired_state(str(tmp_path))
    desired.keycloak_realms = desired.keycloak_realms or []
    desired.keycloak_realms.append(
        KeycloakRealmSpec(
            realm="dataspace",
            display_name="Dataspace",
            clients=[
                KeycloakClientSpec(
                    client_id="control-api",
                    name="Control API",
                )
            ],
        )
    )

    diff = compute_state_diff(desired, ActualState())

    resource_types = {(change.resource_type, change.operation) for change in diff.changes}
    assert ("keycloak_realm", "create") in resource_types
    assert ("keycloak_client", "create") in resource_types


@pytest.mark.asyncio
async def test_control_api_checkpoint_is_revalidated_live():
    class _ControlApiDriverDouble:
        async def get_procedure_status(self, workflow_id: str):
            assert workflow_id == "wf-123"
            return {"status": "RUNNING"}

    present = await _resource_is_present_via_control_api(
        _ControlApiDriverDouble(),
        {"workflow_id": "wf-123", "resource": {"tenant_id": "tenant-a"}},
    )

    assert present is True


@pytest.mark.asyncio
async def test_discover_actual_state_uses_live_namespace_checks(monkeypatch):
    desired = DesiredState(worker_namespaces=["onboarding"])

    class _KubernetesDriverDouble:
        def namespace_exists(self, name: str) -> bool:
            return name == "onboarding"

    class _ControlApiDriverDouble:
        async def close(self) -> None:
            return None

    monkeypatch.setattr("src.commands.plan.KubernetesDriver", _KubernetesDriverDouble)
    monkeypatch.setattr("src.commands.plan.ControlApiDriver", lambda *_args: _ControlApiDriverDouble())

    actual = await discover_actual_state(desired)

    assert actual.worker_namespaces == ["onboarding"]
