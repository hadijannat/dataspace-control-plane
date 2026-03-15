from dataspace_control_plane_core.domains._shared.errors import DomainError, NotFoundError, ConflictError


class OnboardingNotFoundError(NotFoundError):
    pass


class OnboardingAlreadyCompletedError(ConflictError):
    pass


class OnboardingPhaseOrderViolationError(DomainError):
    pass
