"""
ENTERPRISE OVERLAY PACK TEMPLATE
=================================
Enterprise overlay packs let organizations add internal controls on top
of active regulatory and ecosystem packs.

INVARIANT: You may add stricter rules, but you must NEVER weaken an active
regulatory rule. The _shared/reducers.check_override_safety() function will
reject any attempt to downgrade a regulatory rule's severity.

Typical uses:
  - Additional evidence fields required by internal audit
  - Stricter BPN/identifier validation than the base Catena-X rules
  - Enterprise-specific UI schema extensions
  - Internal policy modules that augment (not replace) ecosystem policies

Pack kind conventions:
  pack_kind = "custom"
  activation_scope = "tenant"   (or "legal_entity" for org-wide enforcement)
  default_priority = 10         (custom packs win over regulation and ecosystem)

Required structure:
  __init__.py   (this file, emptied)
  manifest.toml (pack declaration)
  api.py        (MANIFEST + PROVIDERS)
  evidence.py   (EvidenceAugmenter — most enterprise overlays only add evidence)

Optional:
  requirements.py   (add extra rules — must call check_override_safety before returning)
  ui_schema.py      (UiSchemaProvider for operator console extensions)
  hooks.py          (ProcedureHookProvider for internal audit gates)

IMPORTANT — override safety pattern in requirements.py:
  When adding stricter rules that share a rule_id with a regulatory pack, call:

    from dataspace_control_plane_packs._shared.reducers import check_override_safety
    violations = check_override_safety(
        custom_rules=your_rules,
        regulatory_rules=active_regulatory_rules,
    )
    if violations:
        raise ValueError("Custom rules must not weaken regulatory rules: " + str(violations))

Dependency direction (read only — never mutate):
  core/    — canonical domain models and invariants
  schemas/ — pinned normative schema artifacts

Forbidden:
  - HTTP clients, DB connections, Temporal SDK, FastAPI
  - Lowering severity of any rule that exists in an active regulation pack
  - Replacing canonical policy semantics from core/
  - Bypassing active ecosystem trust requirements
"""

# Step 1: Copy manifest.toml.example → manifest.toml, set pack_kind = "custom"
# Step 2: Implement EvidenceAugmenter in evidence.py (add enterprise fields)
# Step 3: If adding extra validation rules, implement RequirementProvider and call
#         check_override_safety() inside requirements() / validate()
# Step 4: Export MANIFEST and PROVIDERS from api.py
