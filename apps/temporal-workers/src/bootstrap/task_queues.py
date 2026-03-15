"""
Task queue name constants.
Each worker group polls one queue. All workers on the same queue
MUST register the same workflow and activity types.
"""
from src.bootstrap.procedure_catalog import import_procedures_package

procedures_pkg = import_procedures_package()
task_queues = __import__(
    "dataspace_control_plane_procedures._shared.task_queues",
    fromlist=[
        "ONBOARDING_QUEUE",
        "MACHINE_TRUST_QUEUE",
        "TWINS_PUBLICATION_QUEUE",
        "CONTRACTS_NEGOTIATION_QUEUE",
        "COMPLIANCE_QUEUE",
        "MAINTENANCE_QUEUE",
    ],
)

ONBOARDING = task_queues.ONBOARDING_QUEUE
MACHINE_TRUST = task_queues.MACHINE_TRUST_QUEUE
TWINS_PUBLICATION = task_queues.TWINS_PUBLICATION_QUEUE
CONTRACTS_NEGOTIATION = task_queues.CONTRACTS_NEGOTIATION_QUEUE
COMPLIANCE = task_queues.COMPLIANCE_QUEUE
MAINTENANCE = task_queues.MAINTENANCE_QUEUE

ALL_QUEUES = [
    ONBOARDING,
    MACHINE_TRUST,
    TWINS_PUBLICATION,
    CONTRACTS_NEGOTIATION,
    COMPLIANCE,
    MAINTENANCE,
]
