"""MX-Port capability graph model.

MX-Port layers (Factory-X specification):
  MX Discovery           — asset/capability discovery
  MX Access & Usage Ctrl — policy-based access control
  MX Gate                — uniform exchange surface
  MX Converter           — semantic conversion (AAS/OPC UA bridging)
  MX Adapter             — business-application attachment

The capability graph is not a fixed stack; each deployment selects the
layers it implements and connects them via typed edges.  The Leo and
Hercules reference profiles are two concrete instantiations.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MxLayer(str, Enum):
    """The five capability layers of the MX-Port (Factory-X specification)."""

    DISCOVERY = "discovery"
    ACCESS_USAGE = "access_usage"
    GATE = "gate"
    CONVERTER = "converter"
    ADAPTER = "adapter"


@dataclass(frozen=True)
class MxCapabilityEdge:
    """A directed capability edge between two MX-Port layers.

    Attributes:
        from_layer: Source layer of this edge.
        to_layer:   Target layer of this edge.
        protocol:   Protocol or interface used across this edge
                    (e.g. ``"dsp"``, ``"dcp"``, ``"aas-rest"``, ``"opc-ua"``).
        optional:   If False the edge is required for conformance.
    """

    from_layer: MxLayer
    to_layer: MxLayer
    protocol: str
    optional: bool = False


@dataclass(frozen=True)
class MxPortGraph:
    """A concrete MX-Port capability graph for a profile or deployment.

    Attributes:
        profile_name: Human-readable name of this profile (e.g. ``"Leo"``).
        layers:       Frozenset of MxLayer values present in this graph.
        edges:        Ordered tuple of capability edges connecting layers.
    """

    profile_name: str
    layers: frozenset[MxLayer]
    edges: tuple[MxCapabilityEdge, ...]

    def has_layer(self, layer: MxLayer) -> bool:
        """Return True if this graph includes ``layer``."""
        return layer in self.layers

    def required_protocols(self) -> set[str]:
        """Return the set of protocol strings used by non-optional edges."""
        return {edge.protocol for edge in self.edges if not edge.optional}
