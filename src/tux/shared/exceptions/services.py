"""Service, cog loading, and hot-reload exceptions."""

from .base import TuxError

__all__ = [
    "TuxCogLoadError",
    "TuxDependencyResolutionError",
    "TuxFileWatchError",
    "TuxHotReloadConfigurationError",
    "TuxHotReloadError",
    "TuxModuleReloadError",
    "TuxServiceError",
]


class TuxServiceError(TuxError):
    """Base exception for service-related errors."""


class TuxCogLoadError(TuxServiceError):
    """Raised when a cog fails to load."""


class TuxHotReloadError(TuxServiceError):
    """Base exception for hot reload errors."""


class TuxDependencyResolutionError(TuxHotReloadError):
    """Raised when dependency resolution fails."""


class TuxFileWatchError(TuxHotReloadError):
    """Raised when file watching fails."""


class TuxModuleReloadError(TuxHotReloadError):
    """Raised when module reloading fails."""


class TuxHotReloadConfigurationError(TuxHotReloadError):
    """Raised when hot reload configuration is invalid."""
