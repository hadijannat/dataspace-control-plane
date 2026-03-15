"""
REGULATION PACK TEMPLATE
========================
Copy this directory and rename it to your regulation name (e.g. ``eidas/``, ``nis2/``,
``cyber_resilience_act/``).

Regulation packs differ from ecosystem packs in these ways:
  - pack_kind = "regulation"
  - Every rule must carry effective_from / effective_to (regulations have legal dates)
  - Delegated / implementing acts belong in delegated_acts/ subpackages
  - Product-group specifics must NOT be hardcoded in core_rules/
  - Use lower default_priority (e.g. 25–35) so regulation rules take precedence over
    ecosystem rules (lower number = higher priority in reducers)

Required structure:
  __init__.py         (this file, emptied)
  manifest.toml       (pack declaration — copy manifest.toml.example and fill in)
  api.py              (MANIFEST + PROVIDERS exported at module level)
  core_rules/         (generic obligations common to all product groups / subjects)
    __init__.py
    requirements.py   (RequirementProvider for core obligations)
    rules/            (YAML rule catalogs with effective_from / effective_to dates)
  delegated_acts/     (product-group specific rule sets, independently versioned)
    __init__.py
    <product_group>/  (one subpackage per delegated/implementing act)
  vocab/pinned/       (normative texts, OJ publications — pin at retrieval time)

Optional files:
  evidence.py         (EvidenceAugmenter if the regulation mandates specific audit fields)
  hooks.py            (ProcedureHookProvider for onboarding/negotiation gates)

Priority guidance:
  default_priority = 25   # regulations block before ecosystems (priority 100)

Override rule (ENFORCED by check_override_safety):
  custom packs layered on top may NOT lower the severity of any rule declared here.

Dependency direction (read only — never mutate):
  core/                  — canonical domain models and invariants
  schemas/               — pinned normative schema artifacts
  docs/compliance-mappings/ — regulation→obligation mappings (reference only)

Forbidden:
  - HTTP clients, DB connections, Temporal SDK, FastAPI
  - Product-group specifics in core_rules/ — put them in delegated_acts/
  - Hardcoded product identifiers in rule payloads
  - Rules without effective_from
"""

# Step 1: Copy manifest.toml.example → manifest.toml, set pack_kind = "regulation"
# Step 2: Implement core obligations in core_rules/requirements.py
# Step 3: Add rule YAML files under core_rules/rules/ with effective_from on every entry
# Step 4: For each delegated/implementing act, add a subpackage under delegated_acts/
# Step 5: Pin regulation texts under vocab/pinned/ with retrieval_date and sha256
# Step 6: Export MANIFEST and PROVIDERS from api.py using PackCapability keys
# Step 7: Place the completed pack under custom/examples/ or custom/org_packs/
#         and the loader will discover it automatically.
