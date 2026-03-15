"""Public import surface for the contracts domain."""
from .model.enums import NegotiationStatus, EntitlementStatus
from .model.value_objects import OfferSnapshot, AgreementRecord, TransferAuthorization
from .model.aggregates import NegotiationCase, Entitlement
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
from .ports import NegotiationRepository, EntitlementRepository, AgreementRegistryPort, CatalogLookupPort
from .services import ContractService

__all__ = [
    "NegotiationStatus", "EntitlementStatus",
    "OfferSnapshot", "AgreementRecord", "TransferAuthorization",
    "NegotiationCase", "Entitlement",
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
    "AgreementRegistryPort", "CatalogLookupPort",
    "ContractService",
]
