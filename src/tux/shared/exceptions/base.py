"""Root and cross-cutting configuration/runtime exceptions."""

__all__ = [
    "TuxConfigurationError",
    "TuxError",
    "TuxGracefulShutdown",
    "TuxRuntimeError",
    "TuxSetupError",
]


class TuxError(Exception):
    """Base exception for all Tux-specific errors."""


class TuxConfigurationError(TuxError):
    """Raised when there's a configuration issue."""


class TuxRuntimeError(TuxError):
    """Raised when there's a runtime issue."""


class TuxSetupError(TuxError):
    """Raised when bot setup fails."""


class TuxGracefulShutdown(TuxError):  # noqa: N818
    """Raised when bot shuts down gracefully."""
