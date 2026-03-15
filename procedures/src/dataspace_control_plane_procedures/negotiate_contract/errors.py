from temporalio.exceptions import ApplicationError


class NegotiationError(ApplicationError):
    pass


class CredentialCheckError(NegotiationError):
    pass


class OfferValidationError(NegotiationError):
    pass


class CounterpartyRejectedError(NegotiationError):
    pass


class AgreementError(NegotiationError):
    pass


class TransferAuthorizationError(NegotiationError):
    pass
