"""Manufacturing-X Access & Usage Control Layer rules.

Defines the normative requirement that every MX-Port deployment must
include an MX Access & Usage Control capability with policy-based
enforcement, and provides a standalone validator.
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

ACCESS_USAGE_REQUIRED = RuleDefinition(
    rule_id="mx:access-usage-layer-required",
    title="MX Access and Usage Control Layer Required",
    severity="error",
    machine_checkable=True,
    source_uri=_SOURCE_URI,
    source_version=_SOURCE_VERSION,
    effective_from=date(2024, 1, 1),
    effective_to=None,
    scope={},
    payload={
        "required_layer": MxLayer.ACCESS_USAGE.value,
        "rationale": (
            "The MX Access & Usage Control layer is mandatory for policy-based "
            "access enforcement in any Manufacturing-X / Factory-X deployment."
        ),
    },
)


class MxAccessUsageRules:
    """Provides and validates the MX Access & Usage Control requirement."""

    RULES: tuple[RuleDefinition, ...] = (ACCESS_USAGE_REQUIRED,)

    def requirements(
        self,
        *,
        context: dict[str, Any],  # noqa: ARG002
        on: date | None = None,
    ) -> list[RuleDefinition]:
        """Return active access/usage control rules."""
        return [r for r in self.RULES if r.is_active(on)]

    def validate(
        self,
        subject: dict[str, Any],
        *,
        context: dict[str, Any],  # noqa: ARG002
        on: date | None = None,
    ) -> ValidationResult:
        """Validate that ``subject`` declares the access/usage control layer.

        Accepts a subject with a ``"graph"`` key (:class:`MxPortGraph`) or
        a ``"layers"`` key containing layer value strings.
        """
        subject_id = subject.get("id", "unknown")
        result = ValidationResult(subject_id=str(subject_id))

        if not ACCESS_USAGE_REQUIRED.is_active(on):
            return result

        graph: MxPortGraph | None = subject.get("graph")
        if graph is not None:
            has_layer = graph.has_layer(MxLayer.ACCESS_USAGE)
        else:
            layers = subject.get("layers", [])
            has_layer = MxLayer.ACCESS_USAGE.value in layers

        if not has_layer:
            result.add(
                RuleViolation(
                    rule_id=ACCESS_USAGE_REQUIRED.rule_id,
                    severity=ACCESS_USAGE_REQUIRED.severity,
                    message=(
                        "Subject does not declare the MX Access & Usage Control "
                        "layer, which is mandatory per the Manufacturing-X / "
                        "Factory-X specification."
                    ),
                    context={"subject_id": str(subject_id)},
                )
            )
        return result


def validate_access_control(
    subject: dict[str, Any],
    context: dict[str, Any],
) -> ValidationResult:
    """Convenience function: validate access/usage layer on a subject dict."""
    return MxAccessUsageRules().validate(subject, context=context)
