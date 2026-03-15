from pathlib import Path

from src.commands.plan import compute_state_diff, load_desired_state
from src.models.actual_state import ActualState, KeycloakRealmActual
from src.models.desired_state import KeycloakClientSpec, KeycloakRealmSpec


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
