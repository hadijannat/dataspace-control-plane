from temporalio.exceptions import ApplicationError


class RotationError(ApplicationError):
    pass


class CredentialEnumerationError(RotationError):
    pass


class ReissuanceError(RotationError):
    pass


class PresentationVerifyError(RotationError):
    pass


class BindingUpdateError(RotationError):
    pass


class RetirementError(RotationError):
    pass
