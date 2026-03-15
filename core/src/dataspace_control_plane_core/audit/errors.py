from dataspace_control_plane_core.domains._shared.errors import DomainError, NotFoundError


class AuditRecordNotFoundError(NotFoundError):
    pass


class AuditSinkUnavailableError(DomainError):
    pass
