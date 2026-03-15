"""Hercules: full MX-Port reference profile.

The Hercules profile activates all five Manufacturing-X capability layers:
Discovery, Access & Usage Control, Gate, Converter, and Adapter.  It
includes OPC UA bridging via the Converter layer and a full AAS REST
surface on the Gate.  All edges except the Adapter attachment are required.
"""
from __future__ import annotations

from ..model import MxCapabilityEdge, MxLayer, MxPortGraph

HERCULES_PROFILE = MxPortGraph(
    profile_name="Hercules",
    layers=frozenset(
        {
            MxLayer.DISCOVERY,
            MxLayer.ACCESS_USAGE,
            MxLayer.GATE,
            MxLayer.CONVERTER,
            MxLayer.ADAPTER,
        }
    ),
    edges=(
        # Discovery → Access & Usage Control (mandatory)
        MxCapabilityEdge(MxLayer.DISCOVERY, MxLayer.ACCESS_USAGE, "dsp", optional=False),
        # Access & Usage Control → Gate (mandatory)
        MxCapabilityEdge(MxLayer.ACCESS_USAGE, MxLayer.GATE, "dcp", optional=False),
        # Gate → Converter: AAS REST exchange (mandatory in Hercules)
        MxCapabilityEdge(MxLayer.GATE, MxLayer.CONVERTER, "aas-rest", optional=False),
        # Converter → Adapter: OPC UA semantic bridge (mandatory in Hercules)
        MxCapabilityEdge(MxLayer.CONVERTER, MxLayer.ADAPTER, "opc-ua", optional=False),
        # Gate → Adapter: direct AAS REST attachment (optional side-channel)
        MxCapabilityEdge(MxLayer.GATE, MxLayer.ADAPTER, "aas-rest", optional=True),
    ),
)
