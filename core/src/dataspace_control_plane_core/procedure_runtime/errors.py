from dataspace_control_plane_core.domains._shared.errors import DomainError, NotFoundError


class ProcedureNotFoundError(NotFoundError):
    pass


class ProcedureAlreadyRunningError(DomainError):
    pass


class UnknownProcedureTypeError(DomainError):
    pass


class ProcedureInputValidationError(DomainError):
    pass
