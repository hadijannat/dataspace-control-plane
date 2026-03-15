# adapters

`adapters/` is the anti-corruption and integration layer for the control plane.
It owns external protocols, vendor SDKs, runtime transports, health probes, and
typed port implementations for `core/`.

## Layout

- `_shared/` contains transport-agnostic support code: config, auth, error
  mapping, retries, pagination, idempotency, health, and serde helpers.
- `dataspace/` contains dataspace protocol and ecosystem adapters.
- `enterprise/` contains source-system and event-ingest adapters.
- `infrastructure/` contains runtime-facing adapters such as Postgres,
  Keycloak, Vault, Temporal, and telemetry.

## Rules

- Adapter packages implement `core/.../ports.py`; they do not define business meaning.
- Raw vendor DTOs stay in `raw_models.py`, `messages.py`, or generated client modules.
- Transport I/O stays in `client.py` or transport-specific modules.
- `ports_impl.py` is the only place allowed to satisfy `core` ports.
- Each concrete adapter package exposes a health probe with a capability descriptor.

## Public Import Surface

- Import package-level APIs from `dataspace_control_plane_adapters.<family>.<adapter>.api`.
- Import top-level lazy loaders and shared factory exports from
  `dataspace_control_plane_adapters.api`.
- Do not import raw DTOs or internal helper modules from `apps/`, `procedures/`,
  or `core/`.

## Verification

- `find adapters -maxdepth 3 -type d | sort`
- `python -m compileall adapters/src`
- `pytest tests/unit/adapters tests/integration/adapters -q`
- `pytest adapters/src/dataspace_control_plane_adapters -q`
