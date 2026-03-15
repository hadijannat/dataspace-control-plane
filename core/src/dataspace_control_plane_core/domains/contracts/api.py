"""Public import surface for the contracts domain."""
from .model.enums import NegotiationStatus, EntitlementStatus
from .model.value_objects import (
    AgreementRecord,
    ContractReference,
    CounterOffer,
    OfferSnapshot,
    TransferAuthorization,
)
from .model.aggregates import AgreementAggregate, Entitlement, NegotiationCase
from .model.invariants import require_counterparty, require_active_entitlement
from .commands import (
    StartNegotiationCommand, SubmitOfferCommand,
    ConcludeAgreementCommand, TerminateNegotiationCommand,
    RevokeEntitlementCommand,
)
from .events import (
    NegotiationStarted, OfferSubmitted, AgreementConcluded,
    NegotiationTerminated, EntitlementRevoked,
)
from .errors import (
    NegotiationNotFoundError, EntitlementNotFoundError,
    NegotiationAlreadyConcludedError, NegotiationTerminatedError,
    EntitlementNotActiveError,
)
from .ports import (
    AgreementRegistryPort,
    CatalogLookupPort,
    EntitlementRepository,
    NegotiationPort,
    NegotiationRepository,
    TransferObservationPort,
)
from .services import ContractService

__all__ = [
    "NegotiationStatus", "EntitlementStatus",
    "OfferSnapshot", "CounterOffer", "AgreementRecord", "ContractReference", "TransferAuthorization",
    "NegotiationCase", "Entitlement", "AgreementAggregate",
    "require_counterparty", "require_active_entitlement",
    "StartNegotiationCommand", "SubmitOfferCommand",
    "ConcludeAgreementCommand", "TerminateNegotiationCommand",
    "RevokeEntitlementCommand",
    "NegotiationStarted", "OfferSubmitted", "AgreementConcluded",
    "NegotiationTerminated", "EntitlementRevoked",
    "NegotiationNotFoundError", "EntitlementNotFoundError",
    "NegotiationAlreadyConcludedError", "NegotiationTerminatedError",
    "EntitlementNotActiveError",
    "NegotiationRepository", "EntitlementRepository",
    "AgreementRegistryPort", "CatalogLookupPort", "NegotiationPort", "TransferObservationPort",
    "ContractService",
]
