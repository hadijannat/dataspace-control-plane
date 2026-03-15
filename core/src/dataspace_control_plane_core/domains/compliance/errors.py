from dataspace_control_plane_core.domains._shared.errors import DomainError, NotFoundError, ConflictError


class ComplianceRecordNotFoundError(NotFoundError):
    pass


class ScanAlreadyRunningError(ConflictError):
    pass
