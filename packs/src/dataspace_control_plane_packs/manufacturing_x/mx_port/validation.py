"""Validation of MX-Port capability graphs.

Checks that a graph satisfies the minimum layer requirements defined by
the Manufacturing-X / Factory-X specification.  Returns a structured
ValidationResult so callers can distinguish errors from warnings.
"""
from __future__ import annotations

from ..._shared.rule_model import RuleViolation, ValidationResult
from .model import MxLayer, MxPortGraph

# Rule IDs that mirror rules/requirements.yaml
_RULE_DISCOVERY = "mx:discovery-layer-required"
_RULE_ACCESS_USAGE = "mx:access-usage-layer-required"
_RULE_GATE = "mx:gate-layer-required"

_SOURCE_URI = (
    "https://www.plattform-i40.de/IP/Navigation/EN/Manufacturing-X/Manufacturing-X.html"
)


def validate_mx_port_graph(graph: MxPortGraph) -> ValidationResult:
    """Validate that ``graph`` satisfies MX-Port layer requirements.

    Required layers (error severity):
      - DISCOVERY
      - ACCESS_USAGE

    Recommended layers (warning severity):
      - GATE

    Returns a :class:`ValidationResult` with subject_id set to the profile
    name.
    """
    result = ValidationResult(subject_id=graph.profile_name)

    if not graph.has_layer(MxLayer.DISCOVERY):
        result.add(
            RuleViolation(
                rule_id=_RULE_DISCOVERY,
                severity="error",
                message=(
                    f"Profile '{graph.profile_name}' is missing the mandatory "
                    "MX Discovery layer."
                ),
                context={"profile": graph.profile_name, "source_uri": _SOURCE_URI},
            )
        )

    if not graph.has_layer(MxLayer.ACCESS_USAGE):
        result.add(
            RuleViolation(
                rule_id=_RULE_ACCESS_USAGE,
                severity="error",
                message=(
                    f"Profile '{graph.profile_name}' is missing the mandatory "
                    "MX Access & Usage Control layer."
                ),
                context={"profile": graph.profile_name, "source_uri": _SOURCE_URI},
            )
        )

    if not graph.has_layer(MxLayer.GATE):
        result.add(
            RuleViolation(
                rule_id=_RULE_GATE,
                severity="warning",
                message=(
                    f"Profile '{graph.profile_name}' does not include the MX Gate "
                    "layer.  Gate is recommended for full interoperability."
                ),
                context={"profile": graph.profile_name, "source_uri": _SOURCE_URI},
            )
        )

    return result
