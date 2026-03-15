from dataspace_control_plane_core.domains._shared.errors import DomainError, NotFoundError

class TrustParticipantNotFoundError(NotFoundError): pass
class InvalidDidError(DomainError): pass
class CredentialVerificationFailedError(DomainError): pass
class UntrustedIssuerError(DomainError): pass
