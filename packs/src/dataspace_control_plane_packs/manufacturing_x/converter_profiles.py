"""MX-Port Converter layer profiles.

The Converter layer performs semantic conversion between formats, most
commonly between AAS and OPC UA information models.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConverterProfile:
    """A Converter layer profile describing a semantic translation capability.

    Attributes:
        converter_id:  Unique identifier for this converter.
        from_format:   Source semantic format (e.g. ``"aas"``, ``"opc-ua"``).
        to_format:     Target semantic format.
        bidirectional: If True the converter handles both directions.
    """

    converter_id: str
    from_format: str
    to_format: str
    bidirectional: bool = False


# ---------------------------------------------------------------------------
# Standard converter profiles
# ---------------------------------------------------------------------------

AAS_TO_OPCUA = ConverterProfile(
    converter_id="converter:aas-to-opcua",
    from_format="aas",
    to_format="opc-ua",
    bidirectional=False,
)
"""AAS → OPC UA one-way semantic converter."""

OPCUA_TO_AAS = ConverterProfile(
    converter_id="converter:opcua-to-aas",
    from_format="opc-ua",
    to_format="aas",
    bidirectional=False,
)
"""OPC UA → AAS one-way semantic converter."""

AAS_OPCUA_BIDIRECTIONAL = ConverterProfile(
    converter_id="converter:aas-opcua-bidirectional",
    from_format="aas",
    to_format="opc-ua",
    bidirectional=True,
)
"""Bidirectional AAS ↔ OPC UA semantic converter."""
