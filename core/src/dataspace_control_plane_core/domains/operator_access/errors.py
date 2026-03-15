from dataspace_control_plane_core.domains._shared.errors import DomainError, PermissionError

class GrantNotFoundError(DomainError): pass
class UnauthorizedError(PermissionError): pass
class EmergencyAccessExpiredError(DomainError): pass
