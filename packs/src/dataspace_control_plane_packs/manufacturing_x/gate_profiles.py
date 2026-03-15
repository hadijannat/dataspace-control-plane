"""MX-Port Gate layer profiles.

The Gate layer is the uniform exchange surface of an MX-Port deployment.
Each gate profile declares which protocols and semantic formats it exposes.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GateProfile:
    """A Gate layer profile for an MX-Port deployment.

    Attributes:
        gate_id:         Unique identifier for this gate profile.
        protocols:       Ordered list of exchange protocols exposed by the gate.
        semantic_format: Primary semantic format for payload encoding
                         (e.g. ``"aas"`` or ``"opc-ua"``).
    """

    gate_id: str
    protocols: tuple[str, ...]
    semantic_format: str

    def __init__(
        self,
        gate_id: str,
        protocols: list[str],
        semantic_format: str,
    ) -> None:
        # Use object.__setattr__ to work around frozen dataclass
        object.__setattr__(self, "gate_id", gate_id)
        object.__setattr__(self, "protocols", tuple(protocols))
        object.__setattr__(self, "semantic_format", semantic_format)


# ---------------------------------------------------------------------------
# Standard gate profiles
# ---------------------------------------------------------------------------

GATE_AAS_REST = GateProfile(
    gate_id="gate:aas-rest",
    protocols=["aas-rest", "http"],
    semantic_format="aas",
)
"""Gate profile exposing an AAS Part 2 REST API surface."""

GATE_OPC_UA = GateProfile(
    gate_id="gate:opc-ua",
    protocols=["opc-ua"],
    semantic_format="opc-ua",
)
"""Gate profile exposing an OPC UA information model surface."""
