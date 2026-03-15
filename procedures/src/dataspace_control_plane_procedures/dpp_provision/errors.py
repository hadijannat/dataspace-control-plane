from temporalio.exceptions import ApplicationError


class DppProvisionError(ApplicationError):
    pass


class SourceSnapshotError(DppProvisionError):
    pass


class SubmodelCompileError(DppProvisionError):
    pass


class CompletenessCheckError(DppProvisionError):
    pass


class DppRegistrationError(DppProvisionError):
    pass


class IdLinkBindingError(DppProvisionError):
    pass
