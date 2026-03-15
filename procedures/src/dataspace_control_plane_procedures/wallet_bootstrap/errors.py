from temporalio.exceptions import ApplicationError


class WalletBootstrapError(ApplicationError):
    pass


class DidRegistrationError(WalletBootstrapError):
    pass


class CredentialRequestError(WalletBootstrapError):
    pass


class PresentationVerificationError(WalletBootstrapError):
    pass


class WalletBindingError(WalletBootstrapError):
    pass
