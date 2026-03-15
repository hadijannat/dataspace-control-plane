from dataspace_control_plane_core.domains._shared.errors import DomainError, NotFoundError

class PolicyNotFoundError(NotFoundError): pass
class PolicyParseError(DomainError): pass
class PolicyCompileError(DomainError): pass
class PolicyEvaluationError(DomainError): pass
class LossyPolicyActivationError(DomainError): pass
