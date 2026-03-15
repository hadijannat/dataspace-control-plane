# custom/ — Developer Scaffolds, Reference Examples, and Organization Packs

This namespace is **not a runtime pack itself**. It provides three kinds of
artifacts for developers who want to build new packs or add organization-specific
overlays.

---

## Subdirectory Overview

### `templates/`

Copy-and-fill scaffolds for each pack kind:

| Template | Use when… |
|---|---|
| `ecosystem_pack/` | Creating a new ecosystem integration (e.g. `idsa/`, `gaia_x_eu/`) |
| `regulation_pack/` | Implementing a regulation overlay (e.g. `nis2/`, `cyber_resilience_act/`) |
| `enterprise_overlay_pack/` | Adding internal enterprise controls on top of existing packs |

Each template contains an `__init__.py` with step-by-step instructions and a
`manifest.toml.example` you copy and fill in.

### `examples/`

Tested, runnable reference implementations:

| Example | Demonstrates |
|---|---|
| `gaiax_federation_overlay/` | `TrustAnchorOverlayProvider` — filtering Gaia-X trust anchors to a federation subset |
| `enterprise_policy_overlay/` | `EvidenceAugmenter` — adding enterprise audit fields to evidence bundles |

Examples are intentionally minimal. They are kept in-tree and run in CI so they
serve as living documentation.

### `org_packs/`

Drop your actual organization-specific pack implementations here. Each org pack
follows the same template structure as `custom/templates/`. In public forks this
directory is gitignored by default — move org-specific packs to a private overlay
repo or add them to `.gitignore` as appropriate.

---

## How to Create a New Custom Pack

1. **Choose the right template.**
   - New ecosystem integration → copy `templates/ecosystem_pack/`
   - New regulation → copy `templates/regulation_pack/`
   - Enterprise overlay → copy `templates/enterprise_overlay_pack/`

2. **Copy the template directory** into `custom/org_packs/<your_pack_id>/`.

3. **Fill in `manifest.toml`.**
   Copy `manifest.toml.example` → `manifest.toml` and fill in `pack_id`,
   `version`, `display_name`, `description`, and the `[[capabilities]]` tables
   for every capability interface you implement. Remove entries for capabilities
   you do not implement.

4. **Implement your capabilities** in the corresponding Python files
   (`requirements.py`, `evidence.py`, etc.). Keep all logic synchronous and
   free of I/O. Use relative imports to access `_shared` types:

   ```python
   from ...._shared.manifest import PackManifest, _minimal_manifest
   from ...._shared.interfaces import EvidenceAugmenter
   from ...._shared.reducers import check_override_safety
   ```

5. **Export `MANIFEST` and `PROVIDERS` from `api.py`.**

   ```python
   MANIFEST: PackManifest = _minimal_manifest(...)
   PROVIDERS: dict[str, Any] = {
       "EvidenceAugmenter": YourAugmenter(),
   }
   ```

6. **Register your pack.** Add it to `BUILTIN_PACKS` in the main
   `loader.py`, or register it via a Python entry-point under the
   `dataspace_control_plane_packs.packs` group.

---

## The "Stricter Only, Never Weaker" Invariant

Custom packs sit at the highest priority level in the reducer chain
(`custom > regulation > ecosystem`). This means custom rules are applied first,
which gives them the power to add stricter controls — but they must **never**
lower the severity of an active regulatory rule.

The `check_override_safety` function in `_shared/reducers` enforces this:

```python
from dataspace_control_plane_packs._shared.reducers import check_override_safety

violations = check_override_safety(
    custom_rules=my_custom_rules,
    regulatory_rules=active_regulatory_rules,
)
if violations:
    raise ValueError(
        "Custom rules must not weaken regulatory requirements: " + str(violations)
    )
```

Call this inside your `RequirementProvider.requirements()` or `.validate()`
whenever your custom rules share a `rule_id` with a regulation pack.

What custom packs **may** do:
- Add new evidence fields with an enterprise-specific namespace prefix
- Add stricter validation rules (same or higher severity than the regulation)
- Add federation-specific Gaia-X trust anchor filters
- Add organization-specific UI metadata

What custom packs **must not** do:
- Lower the `severity` of any rule that exists in an active regulation pack
- Remove or replace canonical policy semantics defined in `core/`
- Bypass active ecosystem trust requirements

---

## Registering a Custom Pack

### Option A — Add to `BUILTIN_PACKS`

In `packs/src/dataspace_control_plane_packs/loader.py`, extend the
`BUILTIN_PACKS` mapping with your pack's module path:

```python
BUILTIN_PACKS = {
    ...
    "example_enterprise_policy_overlay": (
        "dataspace_control_plane_packs.custom.examples.enterprise_policy_overlay.api"
    ),
}
```

### Option B — Python entry-points (recommended for org packs)

In your private overlay package's `pyproject.toml`:

```toml
[project.entry-points."dataspace_control_plane_packs.packs"]
my_org_pack = "my_org.packs.my_pack.api"
```

The pack loader discovers entry-point-registered packs at startup alongside
the built-in packs.

---

## Federation Overlays and the Base Gaia-X Pack

A Gaia-X federation overlay is a `custom`-kind pack that implements
`TrustAnchorOverlayProvider`. It sits alongside (not instead of) the base
`gaia_x` pack.

The base `gaia_x` pack provides the global trust anchor set. The federation
overlay filters that set down to the anchors relevant to one specific
federation. Anchors with no `federation_id` field are global anchors and are
always included by well-behaved federation overlays.

See `examples/gaiax_federation_overlay/api.py` for a minimal runnable
example.

When a federation overlay is active alongside the `gaia_x` pack, the resolver
calls `overlay_anchors(base_anchors)` on every active `TrustAnchorOverlayProvider`
in activation-scope order, so multiple federation overlays can be composed.
