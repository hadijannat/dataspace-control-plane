from temporalio.exceptions import ApplicationError


class RevocationError(ApplicationError):
    pass


class StatusUpdateError(RevocationError):
    pass


class BindingPropagationError(RevocationError):
    pass


class DependentNotificationError(RevocationError):
    pass


class EvidenceError(RevocationError):
    pass
