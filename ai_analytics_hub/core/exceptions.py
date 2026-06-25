class DependencyNotInstalledError(RuntimeError):
    """Raised when an optional runtime dependency required by a module is missing."""


class ExternalServiceConfigurationError(RuntimeError):
    """Raised when a third-party integration is missing required configuration."""


class ExternalServiceRequestError(RuntimeError):
    """Raised when a third-party integration fails at request time."""
