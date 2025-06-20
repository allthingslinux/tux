from typing import TypeVar

from prisma.models import Case


class PermissionLevelError(Exception):
    """Raised when a user doesn't have the required permission level."""

    def __init__(self, permission: str) -> None:
        self.permission = permission
        super().__init__(f"Missing required permission: {permission}")


class AppCommandPermissionLevelError(Exception):
    """Raised when a user doesn't have the required permission level for an app command."""

    def __init__(self, permission: str) -> None:
        self.permission = permission
        super().__init__(f"Missing required permission: {permission}")


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
    BaseException
        If the result is an exception
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

    Raises
    ------
    BaseException
        If the result is an exception
    TypeError
        If the result is not a Case
    """
    return handle_gather_result(case_result, Case)


class APIConnectionError(Exception):
    """Raised when there's an issue connecting to an external API."""

    def __init__(self, service_name: str, original_error: Exception):
        self.service_name = service_name
        self.original_error = original_error
        super().__init__(f"Connection error with {service_name}: {original_error}")


class APIRequestError(Exception):
    """Raised when an API request fails with a specific status code."""

    def __init__(self, service_name: str, status_code: int, reason: str):
        self.service_name = service_name
        self.status_code = status_code
        self.reason = reason
        super().__init__(f"API request to {service_name} failed with status {status_code}: {reason}")


class APIResourceNotFoundError(APIRequestError):
    """Raised when an API request results in a 404 or similar resource not found error."""

    def __init__(self, service_name: str, resource_identifier: str, status_code: int = 404):
        self.resource_identifier = resource_identifier
        super().__init__(
            service_name,
            status_code,
            reason=f"Resource '{resource_identifier}' not found.",
        )


class APIPermissionError(APIRequestError):
    """Raised when an API request fails due to permissions (e.g., 403 Forbidden)."""

    def __init__(self, service_name: str, status_code: int = 403):
        super().__init__(
            service_name,
            status_code,
            reason="API request failed due to insufficient permissions.",
        )


# === Code Execution Exceptions ===


class CodeExecutionError(Exception):
    """Base exception for code execution errors."""


class MissingCodeError(CodeExecutionError):
    """Raised when no code is provided for execution."""

    def __init__(self) -> None:
        super().__init__(
            "Please provide code with syntax highlighting in this format:\n"
            '```\n`\u200b``python\nprint("Hello, World!")\n`\u200b``\n```',
        )


class InvalidCodeFormatError(CodeExecutionError):
    """Raised when code format is invalid."""

    def __init__(self) -> None:
        super().__init__(
            "Please provide code with syntax highlighting in this format:\n"
            '```\n`\u200b``python\nprint("Hello, World!")\n`\u200b``\n```',
        )


class UnsupportedLanguageError(CodeExecutionError):
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

        super().__init__(
            f"No compiler found for `{language}`. The following languages are supported:\n```{available_langs}```",
        )


class CompilationError(CodeExecutionError):
    """Raised when code compilation fails."""

    def __init__(self) -> None:
        super().__init__("Failed to get output from the compiler. The code may have compilation errors.")
