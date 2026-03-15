from temporalio.exceptions import ApplicationError


class TwinRegistrationError(ApplicationError):
    pass


class ShellValidationError(TwinRegistrationError):
    pass


class SubmodelUpsertError(TwinRegistrationError):
    pass


class RegistryRegistrationError(TwinRegistrationError):
    pass


class AccessBindingError(TwinRegistrationError):
    pass


class VerificationError(TwinRegistrationError):
    pass
