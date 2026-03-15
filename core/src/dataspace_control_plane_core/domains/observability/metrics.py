from .model.value_objects import MetricDefinition
from .model.enums import MetricKind

PROCEDURE_STARTED = MetricDefinition(
    "dataspace_procedure_started_total",
    MetricKind.COUNTER,
    "1",
    "Procedures initiated",
    ("procedure_type", "tenant_id"),
)

PROCEDURE_DURATION = MetricDefinition(
    "dataspace_procedure_duration_seconds",
    MetricKind.HISTOGRAM,
    "s",
    "Procedure execution time",
    ("procedure_type", "status"),
)

CONTRACT_NEGOTIATIONS = MetricDefinition(
    "dataspace_contract_negotiations_total",
    MetricKind.COUNTER,
    "1",
    "Contract negotiations",
    ("status", "tenant_id"),
)

ACTIVE_ENTITLEMENTS = MetricDefinition(
    "dataspace_active_entitlements",
    MetricKind.GAUGE,
    "1",
    "Active entitlements",
    ("tenant_id",),
)

COMPLIANCE_GAPS = MetricDefinition(
    "dataspace_compliance_gaps_total",
    MetricKind.GAUGE,
    "1",
    "Open compliance gaps",
    ("severity", "framework", "tenant_id"),
)

DATA_EXCHANGE_BYTES = MetricDefinition(
    "dataspace_data_exchange_bytes_total",
    MetricKind.COUNTER,
    "By",
    "Bytes exchanged",
    ("direction", "tenant_id"),
)

ALL_METRICS: tuple[MetricDefinition, ...] = (
    PROCEDURE_STARTED,
    PROCEDURE_DURATION,
    CONTRACT_NEGOTIATIONS,
    ACTIVE_ENTITLEMENTS,
    COMPLIANCE_GAPS,
    DATA_EXCHANGE_BYTES,
)
