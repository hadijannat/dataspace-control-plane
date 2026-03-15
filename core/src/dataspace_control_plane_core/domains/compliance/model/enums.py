from enum import Enum


class ComplianceFramework(str, Enum):
    DSP_PROTOCOL = "dsp_protocol"
    DCP_PROTOCOL = "dcp_protocol"
    ESPR_DPP = "espr_dpp"
    GDPR = "gdpr"
    GAIA_X_TRUST = "gaia_x_trust"
    CATENA_X_MEMBERSHIP = "catena_x_membership"


class GapSeverity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CompliancePosture(str, Enum):
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    UNKNOWN = "unknown"
