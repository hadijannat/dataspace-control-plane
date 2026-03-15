from temporalio.exceptions import ApplicationError


class ConnectorBootstrapError(ApplicationError):
    pass


class InfraApplyError(ConnectorBootstrapError):
    pass


class HealthCheckError(ConnectorBootstrapError):
    pass


class DataspaceRegistrationError(ConnectorBootstrapError):
    pass


class WalletLinkError(ConnectorBootstrapError):
    pass
