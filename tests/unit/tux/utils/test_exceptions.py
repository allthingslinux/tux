"""Tests for the tux.utils.exceptions module."""

from typing import Any
from unittest.mock import Mock

import pytest
from tux.utils.exceptions import (
    APIConnectionError,
    APIRequestError,
    APIResourceNotFoundError,
    CodeExecutionError,
    MissingCodeError,
    PermissionLevelError,
    UnsupportedLanguageError,
    handle_case_result,
    handle_gather_result,
)

from prisma.models import Case


class TestPermissionLevelError:
    """Test cases for PermissionLevelError."""

    def test_init_sets_permission_and_message(self) -> None:
        """Test that PermissionLevelError stores permission and creates proper message."""
        permission = "manage_messages"
        error = PermissionLevelError(permission)

        assert error.permission == permission
        assert str(error) == "Missing required permission: manage_messages"

    def test_inheritance(self) -> None:
        """Test that PermissionLevelError inherits from Exception."""
        error = PermissionLevelError("test")
        assert isinstance(error, Exception)


class TestAPIExceptions:
    """Test cases for API-related exceptions."""

    def test_api_connection_error(self) -> None:
        """Test APIConnectionError initialization and message."""
        original_error = ConnectionError("Network timeout")
        service = "GitHub API"

        error = APIConnectionError(service, original_error)

        assert error.service_name == service
        assert error.original_error == original_error
        assert str(error) == "Connection error with GitHub API: Network timeout"

    def test_api_request_error(self) -> None:
        """Test APIRequestError initialization and message."""
        service = "Discord API"
        status_code = 429
        reason = "Rate limited"

        error = APIRequestError(service, status_code, reason)

        assert error.service_name == service
        assert error.status_code == status_code
        assert error.reason == reason
        assert str(error) == "API request to Discord API failed with status 429: Rate limited"

    def test_api_resource_not_found_error(self) -> None:
        """Test APIResourceNotFoundError initialization and inheritance."""
        service = "GitHub API"
        resource_id = "user123"

        error = APIResourceNotFoundError(service, resource_id)

        assert error.service_name == service
        assert error.status_code == 404  # Default
        assert error.resource_identifier == resource_id
        assert isinstance(error, APIRequestError)
        assert "Resource 'user123' not found" in str(error)


class TestCodeExecutionExceptions:
    """Test cases for code execution exceptions."""

    def test_missing_code_error(self) -> None:
        """Test MissingCodeError message and inheritance."""
        error = MissingCodeError()

        assert isinstance(error, CodeExecutionError)
        error_msg = str(error)
        assert "Please provide code with syntax highlighting" in error_msg
        assert "python" in error_msg

    def test_unsupported_language_error(self) -> None:
        """Test UnsupportedLanguageError with language and supported languages."""
        language = "brainfuck"
        supported = ["python", "java", "cpp", "javascript"]

        error = UnsupportedLanguageError(language, supported)

        assert isinstance(error, CodeExecutionError)
        assert error.language == language
        assert error.supported_languages == supported

        error_msg = str(error)
        assert f"No compiler found for `{language}`" in error_msg
        assert "python, java, cpp, javascript" in error_msg


class TestHandleGatherResult:
    """Test cases for the handle_gather_result utility function."""

    def test_handle_gather_result_success(self) -> None:
        """Test handle_gather_result with successful result."""
        result = "test_string"
        expected_type = str

        handled = handle_gather_result(result, expected_type)

        assert handled == result
        assert isinstance(handled, str)

    def test_handle_gather_result_with_exception(self) -> None:
        """Test handle_gather_result when result is an exception."""
        original_error = ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            handle_gather_result(original_error, str)

    def test_handle_gather_result_wrong_type(self) -> None:
        """Test handle_gather_result when result type doesn't match expected."""
        result = 42  # int
        expected_type = str

        with pytest.raises(TypeError, match="Expected str but got int"):
            handle_gather_result(result, expected_type)


class TestHandleCaseResult:
    """Test cases for the handle_case_result utility function."""

    def test_handle_case_result_success(self) -> None:
        """Test handle_case_result with a valid Case object."""
        # Create a mock Case object
        mock_case = Mock(spec=Case)
        mock_case.id = "test_case_id"

        result = handle_case_result(mock_case)

        assert result == mock_case
        assert hasattr(result, "id")

    def test_handle_case_result_with_exception(self) -> None:
        """Test handle_case_result when result is an exception."""
        original_error = RuntimeError("Database error")

        with pytest.raises(RuntimeError, match="Database error"):
            handle_case_result(original_error)

    def test_handle_case_result_wrong_type(self) -> None:
        """Test handle_case_result when result is not a Case."""
        wrong_result: Any = "not_a_case"

        with pytest.raises(TypeError, match="Expected Case but got str"):
            handle_case_result(wrong_result)
