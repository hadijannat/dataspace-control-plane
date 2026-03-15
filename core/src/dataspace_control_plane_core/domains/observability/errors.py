from dataspace_control_plane_core.domains._shared.errors import DomainError


class MetricEmitterUnavailableError(DomainError):
    pass


class TracingUnavailableError(DomainError):
    pass
