"""MX-Port DataExchangeProfileProvider.

Derives supported protocols and required capabilities from a concrete
MxPortGraph so the registry can query the profile without knowing its
internal structure.
"""
from __future__ import annotations

from typing import Any

from .model import MxPortGraph


class MxDataExchangeProfileProvider:
    """Implements DataExchangeProfileProvider for an MX-Port graph.

    The provider is constructed with a concrete :class:`MxPortGraph`
    (typically ``LEO_PROFILE`` or ``HERCULES_PROFILE``) and derives its
    answers from the graph's edges and layers.
    """

    def __init__(self, profile: MxPortGraph) -> None:
        self._profile = profile

    # ------------------------------------------------------------------
    # DataExchangeProfileProvider interface
    # ------------------------------------------------------------------

    def supported_protocols(self) -> list[str]:
        """Return deduplicated protocol strings from all edges in the graph."""
        seen: set[str] = set()
        result: list[str] = []
        for edge in self._profile.edges:
            if edge.protocol not in seen:
                seen.add(edge.protocol)
                result.append(edge.protocol)
        return result

    def required_capabilities(self, *, context: dict[str, Any]) -> list[str]:  # noqa: ARG002
        """Return layer names of all non-optional (required) layers.

        The ``context`` parameter is accepted for interface compatibility
        but is not used; MX-Port layer requirements are profile-static.
        """
        return [
            layer.value
            for layer in self._profile.layers
            if layer.value in self._required_layer_values()
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _required_layer_values(self) -> set[str]:
        """Determine which layers are 'required' from the edge optionality map.

        A layer is required if it is the *from_layer* of at least one
        non-optional edge, or the *to_layer* of at least one non-optional edge.
        This is a conservative definition: if a layer participates in any
        mandatory data-flow it cannot be omitted.
        """
        required: set[str] = set()
        for edge in self._profile.edges:
            if not edge.optional:
                required.add(edge.from_layer.value)
                required.add(edge.to_layer.value)
        return required
