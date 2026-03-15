from temporalio.exceptions import ApplicationError


class DelegationError(ApplicationError):
    pass


class TopologyCreationError(DelegationError):
    pass


class IdentifierBindingError(DelegationError):
    pass


class ConnectorModeError(DelegationError):
    pass


class TrustScopeError(DelegationError):
    pass


class DelegationVerificationError(DelegationError):
    pass
