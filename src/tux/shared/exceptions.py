"""
Custom Exceptions for Tux Bot.

This module defines all custom exception classes used throughout the Tux Discord bot,
including database errors, permission errors, API errors, and validation errors.
"""

from typing import TypeVar

from tux.database.models import Case

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
    "handle_case_result",
    "handle_gather_result",
]

# === Base Exceptions ===


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


# === Database Exceptions ===


class TuxDatabaseError(TuxError):
    """Base exception for database-related errors."""


class TuxDatabaseConnectionError(TuxDatabaseError):
    """Raised when database connection fails."""

    def __init__(
        self,
        message: str = "Database connection failed",
        original_error: Exception | None = None,
    ):
        """Initialize the database connection error.

        Parameters
        ----------
        message : str, optional
            Error message, by default "Database connection failed".
        original_error : Exception, optional
            The original exception that caused this error, by default None.
        """
        self.original_error = original_error
        super().__init__(message)


class TuxDatabaseMigrationError(TuxDatabaseError):
    """Raised when database migration fails."""


class TuxDatabaseQueryError(TuxDatabaseError):
    """Raised when a database query fails."""


# === Permission Exceptions ===


class TuxPermissionError(TuxError):
    """Base exception for permission-related errors."""


class TuxPermissionLevelError(TuxPermissionError):
    """Raised when a user doesn't have the required permission rank."""

    def __init__(self, permission: str) -> None:
        """Initialize the permission level error.

        Parameters
        ----------
        permission : str
            The name of the required permission that was missing.
        """
        self.permission = permission
        super().__init__(f"Missing required permission: {permission}")


class TuxAppCommandPermissionLevelError(TuxPermissionError):
    """Raised when a user doesn't have the required permission rank for an app command."""

    def __init__(self, permission: str) -> None:
        """Initialize the app command permission level error.

        Parameters
        ----------
        permission : str
            The name of the required permission that was missing for the app command.
        """
        self.permission = permission
        super().__init__(f"Missing required permission: {permission}")


class TuxPermissionDeniedError(TuxPermissionError):
    """Raised when a user doesn't have permission to run a command (dynamic system)."""

    def __init__(
        self,
        required_rank: int,
        user_rank: int,
        command_name: str | None = None,
    ):
        """Initialize the permission denied error.

        Parameters
        ----------
        required_rank : int
            The minimum permission rank required to run the command.
        user_rank : int
            The actual permission rank of the user.
        command_name : str, optional
            The name of the command that was attempted, by default None.
        """
        self.required_rank = required_rank
        self.user_rank = user_rank
        self.command_name = command_name

        if command_name:
            message = f"You need permission rank **{required_rank}** to use `{command_name}`. Your rank: **{user_rank}**"
        else:
            message = f"You need permission rank **{required_rank}**. Your rank: **{user_rank}**"

        super().__init__(message)


# === API Exceptions ===


class TuxAPIError(TuxError):
    """Base exception for API-related errors."""


class TuxAPIConnectionError(TuxAPIError):
    """Raised when there's an issue connecting to an external API."""

    def __init__(self, service_name: str, original_error: Exception) -> None:
        """Initialize the API connection error.

        Parameters
        ----------
        service_name : str
            Name of the service that failed to connect.
        original_error : Exception
            The original exception that caused the connection failure.
        """
        self.service_name = service_name
        self.original_error = original_error
        super().__init__(f"Connection error with {service_name}: {original_error}")


class TuxAPIRequestError(TuxAPIError):
    """Raised when an API request fails with a specific status code."""

    def __init__(self, service_name: str, status_code: int, reason: str) -> None:
        """Initialize the API request error.

        Parameters
        ----------
        service_name : str
            Name of the service that the request failed for.
        status_code : int
            HTTP status code of the failed request.
        reason : str
            Reason for the request failure.
        """
        self.service_name = service_name
        self.status_code = status_code
        self.reason = reason
        super().__init__(
            f"API request to {service_name} failed with status {status_code}: {reason}",
        )


class TuxAPIResourceNotFoundError(TuxAPIRequestError):
    """Raised when an API request results in a 404 or similar resource not found error."""

    def __init__(
        self,
        service_name: str,
        resource_identifier: str,
        status_code: int = 404,
    ) -> None:
        """Initialize the API resource not found error.

        Parameters
        ----------
        service_name : str
            Name of the service that was queried.
        resource_identifier : str
            Identifier of the resource that was not found.
        status_code : int, optional
            HTTP status code, by default 404.
        """
        self.resource_identifier = resource_identifier
        super().__init__(
            service_name,
            status_code,
            reason=f"Resource '{resource_identifier}' not found.",
        )


class TuxAPIPermissionError(TuxAPIRequestError):
    """Raised when an API request fails due to permissions (e.g., 403 Forbidden)."""

    def __init__(self, service_name: str, status_code: int = 403) -> None:
        """Initialize the API permission error.

        Parameters
        ----------
        service_name : str
            Name of the service that rejected the request.
        status_code : int, optional
            HTTP status code, by default 403.
        """
        super().__init__(
            service_name,
            status_code,
            reason="API request failed due to insufficient permissions.",
        )


# === Code Execution Exceptions ===


class TuxCodeExecutionError(TuxError):
    """Base exception for code execution errors."""


class TuxMissingCodeError(TuxCodeExecutionError):
    """Raised when no code is provided for execution."""

    def __init__(self) -> None:
        """Initialize the missing code error with usage instructions."""
        super().__init__(
            "Please provide code with syntax highlighting in this format:\n"
            '```\n`\u200b``python\nprint("Hello, World!")\n`\u200b``\n```',
        )


class TuxInvalidCodeFormatError(TuxCodeExecutionError):
    """Raised when code format is invalid."""

    def __init__(self) -> None:
        """Initialize the invalid code format error with usage instructions."""
        super().__init__(
            "Please provide code with syntax highlighting in this format:\n"
            '```\n`\u200b``python\nprint("Hello, World!")\n`\u200b``\n```',
        )


class TuxUnsupportedLanguageError(TuxCodeExecutionError):
    """Raised when the specified language is not supported."""

    def __init__(self, language: str, supported_languages: list[str]) -> None:
        """
        Initialize with language-specific error message.

        Parameters
        ----------
        language : str
            The unsupported language that was requested.
        supported_languages : list[str]
            List of supported language names.
        """
        self.language = language
        self.supported_languages = supported_languages
        available_langs = ", ".join(supported_languages)

        # Sanitize language input to prevent formatting issues in error messages
        # Extract first word (language name) and truncate to prevent malicious/long inputs
        language_str = language.strip()
        # Get first word only (language names are typically single words)
        first_word = language_str.split()[0] if language_str.split() else language_str
        # Truncate to max 30 characters to prevent extremely long inputs
        sanitized_language = first_word[:30] if len(first_word) > 30 else first_word

        super().__init__(
            f"No compiler found for `{sanitized_language}`. The following languages are supported:\n```{available_langs}```",
        )


class TuxCompilationError(TuxCodeExecutionError):
    """Raised when code compilation fails."""

    def __init__(self) -> None:
        """Initialize the compilation error with default message."""
        super().__init__(
            "Failed to get output from the compiler. The code may have compilation errors.",
        )


# === Service Exceptions ===


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


# === Utility Functions ===

T = TypeVar("T")


def handle_gather_result(result: T | BaseException, expected_type: type[T]) -> T:
    """Handle a result from asyncio.gather with return_exceptions=True.

    Parameters
    ----------
    result : T | BaseException
        The result from asyncio.gather
    expected_type : type[T]
        The expected type of the result

    Returns
    -------
    T
        The result if it matches the expected type

    Raises
    ------
    TypeError
        If the result is not of the expected type
    """
    if isinstance(result, BaseException):
        raise result
    if not isinstance(result, expected_type):
        msg = f"Expected {expected_type.__name__} but got {type(result).__name__}"
        raise TypeError(msg)
    return result


def handle_case_result(case_result: Case | BaseException) -> Case:
    """Handle a case result from asyncio.gather with return_exceptions=True.

    Parameters
    ----------
    case_result : Case | BaseException
        The case result from asyncio.gather

    Returns
    -------
    Case
        The case if valid
    """
    return handle_gather_result(case_result, Case)
