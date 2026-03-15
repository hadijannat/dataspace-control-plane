"""Public API surface for the Manufacturing-X / Factory-X ecosystem pack.

Import from here to obtain the pack manifest, provider instances, and all
public domain types.  Direct imports from submodules are also supported but
this module is the stable surface.
"""
from __future__ import annotations

from pathlib import Path

from .._shared.manifest import PackManifest

# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

MANIFEST: PackManifest = PackManifest.from_toml(
    Path(__file__).parent / "manifest.toml"
)

# ---------------------------------------------------------------------------
# Capability providers (instantiated once — they carry no mutable state)
# ---------------------------------------------------------------------------

from .requirements import MxRequirementProvider as MxRequirementProvider
from .mx_port.capabilities import MxDataExchangeProfileProvider as _MxDataExchangeProfileProvider
from .aas_dpp4o_bridge import MxTwinTemplateProvider as MxTwinTemplateProvider
from .evidence import MxEvidenceAugmenter as MxEvidenceAugmenter

# Default DataExchangeProfileProvider uses the Hercules (full) profile so that
# the registry advertises all protocols; callers that only need Leo can
# instantiate _MxDataExchangeProfileProvider(LEO_PROFILE) directly.
from .mx_port.profiles.hercules import HERCULES_PROFILE as _HERCULES_PROFILE

MxDataExchangeProfileProvider = _MxDataExchangeProfileProvider(_HERCULES_PROFILE)

# Registry-compatible provider dict
PROVIDERS: dict[str, object] = {
    "RequirementProvider": MxRequirementProvider(),
    "DataExchangeProfileProvider": MxDataExchangeProfileProvider,
    "TwinTemplateProvider": MxTwinTemplateProvider(),
    "EvidenceAugmenter": MxEvidenceAugmenter(),
}

# ---------------------------------------------------------------------------
# Re-exports: domain types
# ---------------------------------------------------------------------------

from .mx_port.model import MxCapabilityEdge as MxCapabilityEdge
from .mx_port.model import MxLayer as MxLayer
from .mx_port.model import MxPortGraph as MxPortGraph
from .mx_port.profiles.leo import LEO_PROFILE as LEO_PROFILE
from .mx_port.profiles.hercules import HERCULES_PROFILE as HERCULES_PROFILE
from .mx_port.validation import validate_mx_port_graph as validate_mx_port_graph
from .gate_profiles import GateProfile as GateProfile
from .gate_profiles import GATE_AAS_REST as GATE_AAS_REST
from .gate_profiles import GATE_OPC_UA as GATE_OPC_UA
from .converter_profiles import ConverterProfile as ConverterProfile
from .converter_profiles import AAS_TO_OPCUA as AAS_TO_OPCUA
from .converter_profiles import OPCUA_TO_AAS as OPCUA_TO_AAS
from .adapter_profiles import AdapterProfile as AdapterProfile
from .adapter_profiles import SHOP_FLOOR_ADAPTER as SHOP_FLOOR_ADAPTER
from .adapter_profiles import ERP_ADAPTER as ERP_ADAPTER
from .discovery_rules import MxDiscoveryRules as MxDiscoveryRules
from .discovery_rules import DISCOVERY_REQUIRED as DISCOVERY_REQUIRED
from .access_usage_rules import MxAccessUsageRules as MxAccessUsageRules
from .access_usage_rules import ACCESS_USAGE_REQUIRED as ACCESS_USAGE_REQUIRED

__all__ = [
    "MANIFEST",
    "PROVIDERS",
    # Providers
    "MxRequirementProvider",
    "MxDataExchangeProfileProvider",
    "MxTwinTemplateProvider",
    "MxEvidenceAugmenter",
    # Domain model
    "MxLayer",
    "MxCapabilityEdge",
    "MxPortGraph",
    "LEO_PROFILE",
    "HERCULES_PROFILE",
    "validate_mx_port_graph",
    # Gate
    "GateProfile",
    "GATE_AAS_REST",
    "GATE_OPC_UA",
    # Converter
    "ConverterProfile",
    "AAS_TO_OPCUA",
    "OPCUA_TO_AAS",
    # Adapter
    "AdapterProfile",
    "SHOP_FLOOR_ADAPTER",
    "ERP_ADAPTER",
    # Rules
    "MxDiscoveryRules",
    "DISCOVERY_REQUIRED",
    "MxAccessUsageRules",
    "ACCESS_USAGE_REQUIRED",
]
