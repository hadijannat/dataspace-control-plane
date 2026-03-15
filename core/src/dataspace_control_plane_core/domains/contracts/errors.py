from dataspace_control_plane_core.domains._shared.errors import (
    DomainError, NotFoundError, ConflictError,
)


class NegotiationNotFoundError(NotFoundError):
    pass


class EntitlementNotFoundError(NotFoundError):
    pass


class NegotiationAlreadyConcludedError(ConflictError):
    pass


class NegotiationTerminatedError(DomainError):
    pass


class EntitlementNotActiveError(DomainError):
    pass
