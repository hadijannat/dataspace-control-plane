Installable domain kernel for the dataspace control plane.

Install with `pip install -e core/` and import via `dataspace_control_plane_core`.

Key rules:
- `core/` owns semantic meaning, not transport, storage, or worker bootstrapping.
- Public imports should come from `dataspace_control_plane_core.api` or each package's `api.py`.
- `canonical_models/` contains standards-facing Pydantic schemas.
- `domains/_shared/` contains immutable IDs, clocks, events, aggregate bases, and repository protocols.
- `procedure_runtime/` defines durable-execution contracts and Temporal-adjacent bindings only.
- `audit/` defines append-only evidentiary records, manifests, hashing/signing references, and export contracts.

Compatibility:
- Existing internal import paths like `domains.*.model.*`, `audit.record`, and `procedure_runtime.contracts` remain as deprecated shims for one migration cycle.

See `core/DEPENDENCY_NOTES.md` for required downstream follow-up in `adapters/`, `procedures/`, `apps/temporal-workers`, `tests/`, and `docs/`.
