"""Leo: minimal MX-Port reference profile.

The Leo profile covers the three mandatory layers required for basic
Manufacturing-X interoperability: Discovery, Access & Usage Control, and
Gate.  Converter and Adapter layers are absent or treated as optional
attachments.
"""
from __future__ import annotations

from ..model import MxCapabilityEdge, MxLayer, MxPortGraph

LEO_PROFILE = MxPortGraph(
    profile_name="Leo",
    layers=frozenset({MxLayer.DISCOVERY, MxLayer.ACCESS_USAGE, MxLayer.GATE}),
    edges=(
        MxCapabilityEdge(MxLayer.DISCOVERY, MxLayer.ACCESS_USAGE, "dsp", optional=False),
        MxCapabilityEdge(MxLayer.ACCESS_USAGE, MxLayer.GATE, "dcp", optional=False),
        MxCapabilityEdge(MxLayer.GATE, MxLayer.ADAPTER, "aas-rest", optional=True),
    ),
)
