"""Manufacturing-X Discovery Layer rules.

Defines the normative requirement that every MX-Port deployment must
include an MX Discovery capability, and provides a standalone validator
that can be invoked before constructing the full requirement provider.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .._shared.rule_model import RuleDefinition, RuleViolation, ValidationResult
from .mx_port.model import MxLayer, MxPortGraph

_SOURCE_URI = (
    "https://www.plattform-i40.de/IP/Navigation/EN/Manufacturing-X/Manufacturing-X.html"
)
_SOURCE_VERSION = "2024"

DISCOVERY_REQUIRED = RuleDefinition(
    rule_id="mx:discovery-layer-required",
    title="MX Discovery Layer Required",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=date(2024, 1, 1),
    effective_to=None,
    scope={},
    payload={
        "required_layer": MxLayer.DISCOVERY.value,
        "rationale": (
            "The MX Discovery layer is mandatory for asset and capability "
            "discovery in any Manufacturing-X / Factory-X deployment."
        ),
    },
)


class MxDiscoveryRules:
    """Provides and validates the MX Discovery Layer requirement."""

    RULES: tuple[RuleDefinition, ...] = (DISCOVERY_REQUIRED,)

    def requirements(
        self,
        *,
        context: dict[str, Any],  # noqa: ARG002
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return active discovery rules."""
        return [r for r in self.RULES if r.is_active(on)]

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],  # noqa: ARG002
        on: date | None = None,
    ) -> ValidationResult:
        """Validate that ``subject`` declares the discovery layer.

        Expects ``subject`` to contain a ``"graph"`` key holding an
        :class:`MxPortGraph`, or falls back to a ``"layers"`` list of
        layer value strings.
        """
        subject_id = subject.get("id", "unknown")
        result = ValidationResult(subject_id=str(subject_id))

        if not DISCOVERY_REQUIRED.is_active(on):
            return result

        graph: MxPortGraph | None = subject.get("graph")
        if graph is not None:
            has_discovery = graph.has_layer(MxLayer.DISCOVERY)
        else:
            layers = subject.get("layers", [])
            has_discovery = MxLayer.DISCOVERY.value in layers

        if not has_discovery:
            result.add(
                RuleViolation(
                    rule_id=DISCOVERY_REQUIRED.rule_id,
                    severity=DISCOVERY_REQUIRED.severity,
                    message=(
                        "Subject does not declare the MX Discovery layer, which is "
                        "mandatory per the Manufacturing-X / Factory-X specification."
                    ),
                    context={"subject_id": str(subject_id)},
                )
            )
        return result


def validate_discovery_capability(
    graph: MxPortGraph,
    context: dict[str, Any],
) -> ValidationResult:
    """Convenience function: validate discovery layer on a graph directly."""
    return MxDiscoveryRules().validate({"id": graph.profile_name, "graph": graph}, context=context)
