"""Dataspace Control Plane procedure package."""

from dataspace_control_plane_procedures.registry import (
    ProcedureDefinition,
    discover_definitions,
    get_definition,
)

__version__ = "0.1.0"

__all__ = [
    "ProcedureDefinition",
    "discover_definitions",
    "get_definition",
]
