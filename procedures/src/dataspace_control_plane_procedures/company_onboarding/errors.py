from temporalio.exceptions import ApplicationError


class OnboardingError(ApplicationError):
    pass


class PreflightValidationError(OnboardingError):
    pass


class RegistrationRejectedError(OnboardingError):
    pass


class TrustBootstrapError(OnboardingError):
    pass


class ConnectorBootstrapError(OnboardingError):
    pass
