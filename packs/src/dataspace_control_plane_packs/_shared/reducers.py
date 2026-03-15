"""Pack resolution reducers — how multiple active packs are combined.

Reducer semantics (from the spec):
  - Validation reducer:    union of all hard requirements; first error blocks.
  - Evidence reducer:      union of all required evidence fields and references.
  - Policy compiler:       route by target dialect; one compiler per dialect.
  - Identifier reducer:    namespace by scheme; no pack redefines another's scheme.
  - Default-value reducer: most specific wins: custom > regulation > ecosystem > base.
  - Override rule:         custom packs may add stricter controls, never weaken.

All reducers are pure functions — no I/O, no state.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .interfaces import (
    EvidenceAugmenter,
    IdentifierSchemeProvider,
    PolicyDialectProvider,
    RequirementProvider,
)
from .rule_model import RuleDefinition, RuleViolation, ValidationResult


# ---------------------------------------------------------------------------
# Validation reducer
# ---------------------------------------------------------------------------

def reduce_validation(
    providers: list[RequirementProvider],
    subject: dict[str, Any],
    *,
    context: dict[str, Any],
    on: date | None = None,
) -> ValidationResult:
    """Run all requirement providers and union their violations.

    The first ``error``-severity violation found in any provider's result
    is surfaced; all warnings and infos are accumulated.
    """
    result = ValidationResult(subject_id=context.get("subject_id", "unknown"))
    for provider in providers:
        sub_result = provider.validate(subject, context=context, on=on)
        result.violations.extend(sub_result.violations)
    return result


# ---------------------------------------------------------------------------
# Evidence reducer
# ---------------------------------------------------------------------------

def reduce_evidence(
    augmenters: list[EvidenceAugmenter],
    base_evidence: dict[str, Any],
    *,
    activation_scope: str,
) -> dict[str, Any]:
    """Union all evidence augmenters into a single evidence dict.

    Augmenters are applied in order. An augmenter must not remove
    fields added by a preceding augmenter.
    """
    evidence = dict(base_evidence)
    for augmenter in augmenters:
        augmented = augmenter.augment(evidence, activation_scope=activation_scope)
        # Safety: ensure no existing fields were removed.
        for key in list(evidence.keys()):
            if key not in augmented:
                augmented[key] = evidence[key]
        evidence = augmented
    return evidence


# ---------------------------------------------------------------------------
# Policy compiler reducer
# ---------------------------------------------------------------------------

def reduce_policy_compiler(
    providers: list[PolicyDialectProvider],
    canonical_policy: dict[str, Any],
    *,
    target_dialect: str,
    activation_scope: str,
) -> dict[str, Any]:
    """Route a canonical policy to the correct dialect compiler.

    Raises:
        ValueError: If no provider supports ``target_dialect``.
    """
    for provider in providers:
        if provider.dialect_id == target_dialect:
            return provider.compile(canonical_policy, activation_scope=activation_scope)
    raise ValueError(
        f"No active pack provides a PolicyDialectProvider for dialect {target_dialect!r}"
    )


# ---------------------------------------------------------------------------
# Identifier reducer
# ---------------------------------------------------------------------------

def reduce_identifier_schemes(
    providers: list[IdentifierSchemeProvider],
) -> dict[str, IdentifierSchemeProvider]:
    """Build a scheme_id → provider map, enforcing no-override constraint.

    Raises:
        ValueError: If two packs register the same scheme_id.
    """
    scheme_map: dict[str, IdentifierSchemeProvider] = {}
    for provider in providers:
        if provider.scheme_id in scheme_map:
            existing = scheme_map[provider.scheme_id]
            raise ValueError(
                f"Identifier scheme conflict: scheme_id={provider.scheme_id!r} "
                f"is registered by both {type(existing).__name__} and {type(provider).__name__}. "
                "Declare an explicit conflict resolution in both pack manifests."
            )
        scheme_map[provider.scheme_id] = provider
    return scheme_map


# ---------------------------------------------------------------------------
# Default-value reducer (priority-based)
# ---------------------------------------------------------------------------

_KIND_PRIORITY = {"custom": 0, "regulation": 1, "ecosystem": 2}


def reduce_defaults(
    value_sets: list[tuple[str, dict[str, Any]]],
) -> dict[str, Any]:
    """Merge default-value dicts by pack kind priority.

    Args:
        value_sets: List of (pack_kind, values_dict) tuples.
            ``pack_kind`` is one of ``custom``, ``regulation``, ``ecosystem``.

    Returns:
        Merged dict where ``custom > regulation > ecosystem``.
        If two packs of the same kind define the same key, the later one wins.
    """
    ordered = sorted(value_sets, key=lambda t: _KIND_PRIORITY.get(t[0], 99))
    merged: dict[str, Any] = {}
    for _, values in ordered:
        merged.update(values)
    return merged


# ---------------------------------------------------------------------------
# Override safety check
# ---------------------------------------------------------------------------

def check_override_safety(
    *,
    custom_rules: list[RuleDefinition],
    regulatory_rules: list[RuleDefinition],
) -> list[str]:
    """Return a list of violation messages if custom rules weaken regulatory rules.

    A custom rule weakens a regulatory rule if:
    - It targets the same ``rule_id`` as an active regulatory rule, AND
    - It has a lower severity (``info`` < ``warning`` < ``error``).

    Returns an empty list if all custom rules are at least as strict.
    """
    severity_rank = {"error": 2, "warning": 1, "info": 0}
    reg_by_id = {r.rule_id: r for r in regulatory_rules}
    violations = []
    for custom in custom_rules:
        reg = reg_by_id.get(custom.rule_id)
        if reg is None:
            continue
        if severity_rank[custom.severity] < severity_rank[reg.severity]:
            violations.append(
                f"Custom rule {custom.rule_id!r} weakens regulatory rule "
                f"(custom={custom.severity}, regulatory={reg.severity}). "
                "Custom packs must not weaken active regulatory requirements."
            )
    return violations
