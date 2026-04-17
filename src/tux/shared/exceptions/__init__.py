"""Tux-specific exception types.

This package defines only exception classes. For asyncio gather helpers:

- ``tux.shared.asyncio_gather.handle_gather_result`` — generic typing guard
- ``tux.database.gather_results.handle_case_result`` — when results are ``Case`` instances
"""

from .api import (
    TuxAPIConnectionError,
    TuxAPIError,
    TuxAPIPermissionError,
    TuxAPIRequestError,
    TuxAPIResourceNotFoundError,
)
from .base import (
    TuxConfigurationError,
    TuxError,
    TuxGracefulShutdown,
    TuxRuntimeError,
    TuxSetupError,
)
from .database import (
    TuxDatabaseConnectionError,
    TuxDatabaseError,
    TuxDatabaseMigrationError,
    TuxDatabaseQueryError,
)
from .execution import (
    TuxCodeExecutionError,
    TuxCompilationError,
    TuxInvalidCodeFormatError,
    TuxMissingCodeError,
    TuxUnsupportedLanguageError,
)
from .permissions import (
    TuxAppCommandPermissionLevelError,
    TuxPermissionDeniedError,
    TuxPermissionError,
    TuxPermissionLevelError,
)
from .services import (
    TuxCogLoadError,
    TuxDependencyResolutionError,
    TuxFileWatchError,
    TuxHotReloadConfigurationError,
    TuxHotReloadError,
    TuxModuleReloadError,
    TuxServiceError,
)

__all__ = [
    "TuxAPIConnectionError",
    "TuxAPIError",
    "TuxAPIPermissionError",
    "TuxAPIRequestError",
    "TuxAPIResourceNotFoundError",
    "TuxAppCommandPermissionLevelError",
    "TuxCodeExecutionError",
    "TuxCogLoadError",
    "TuxCompilationError",
    "TuxConfigurationError",
    "TuxDatabaseConnectionError",
    "TuxDatabaseError",
    "TuxDatabaseMigrationError",
    "TuxDatabaseQueryError",
    "TuxDependencyResolutionError",
    "TuxError",
    "TuxFileWatchError",
    "TuxGracefulShutdown",
    "TuxHotReloadConfigurationError",
    "TuxHotReloadError",
    "TuxInvalidCodeFormatError",
    "TuxMissingCodeError",
    "TuxModuleReloadError",
    "TuxPermissionDeniedError",
    "TuxPermissionError",
    "TuxPermissionLevelError",
    "TuxRuntimeError",
    "TuxServiceError",
    "TuxSetupError",
    "TuxUnsupportedLanguageError",
]
