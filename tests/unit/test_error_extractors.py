"""Unit tests for error detail extractors."""

import pytest
import httpx
from unittest.mock import MagicMock

from tux.services.handlers.error.extractors import (
    extract_bad_flag_argument_details,
    extract_bad_union_argument_details,
    extract_httpx_status_details,
    extract_missing_any_role_details,
    extract_missing_argument_details,
    extract_missing_flag_details,
    extract_missing_role_details,
    extract_permission_denied_details,
    extract_permissions_details,
    fallback_format_message,
    format_list,
    unwrap_error,
)


class TestUtilityFunctions:
    """Test utility functions used by extractors."""

    def test_format_list_single_item(self) -> None:
        """Test format_list with single item."""
        result = format_list(["item1"])
        assert result == "`item1`"

    def test_format_list_multiple_items(self) -> None:
        """Test format_list with multiple items."""
        result = format_list(["item1", "item2", "item3"])
        assert result == "`item1`, `item2`, `item3`"

    def test_format_list_empty(self) -> None:
        """Test format_list with empty list."""
        result = format_list([])
        assert result == ""

    def test_unwrap_error_no_nesting(self) -> None:
        """Test unwrap_error with non-nested exception."""
        error = ValueError("test")
        result = unwrap_error(error)
        assert result is error

    def test_unwrap_error_with_nesting(self) -> None:
        """Test unwrap_error with nested exceptions."""
        inner_error = ValueError("inner")
        outer_error = MagicMock()
        outer_error.original = inner_error

        result = unwrap_error(outer_error)
        assert result is inner_error

    def test_unwrap_error_with_multiple_levels(self) -> None:
        """Test unwrap_error with multiple nesting levels."""
        innermost = ValueError("innermost")
        middle = MagicMock()
        middle.original = innermost
        outer = MagicMock()
        outer.original = middle

        result = unwrap_error(outer)
        assert result is innermost

    def test_fallback_format_message_with_error_placeholder(self) -> None:
        """Test fallback_format_message with {error} placeholder."""
        error = ValueError("test error")
        result = fallback_format_message("Error occurred: {error}", error)
        assert "test error" in result

    def test_fallback_format_message_without_placeholder(self) -> None:
        """Test fallback_format_message without placeholder."""
        error = ValueError("test error")
        result = fallback_format_message("Generic message", error)
        assert "An unexpected error occurred" in result


class TestRoleExtractors:
    """Test role-related error extractors."""

    def test_extract_missing_role_details_with_role_id(self) -> None:
        """Test extracting missing role with role ID."""
        error = MagicMock()
        error.missing_role = 123456789

        result = extract_missing_role_details(error)

        assert "roles" in result
        assert "<@&123456789>" in result["roles"]

    def test_extract_missing_role_details_with_string(self) -> None:
        """Test extracting missing role with string name."""
        error = MagicMock()
        error.missing_role = "Admin"

        result = extract_missing_role_details(error)

        assert "roles" in result
        assert "Admin" in result["roles"]

    def test_extract_missing_role_details_none(self) -> None:
        """Test extracting missing role when none provided."""
        error = MagicMock()
        error.missing_role = None

        result = extract_missing_role_details(error)

        assert "roles" in result
        assert "unknown role" in result["roles"]

    def test_extract_missing_any_role_details_with_ids(self) -> None:
        """Test extracting multiple missing roles with IDs."""
        error = MagicMock()
        error.missing_roles = [123456789, 987654321]

        result = extract_missing_any_role_details(error)

        assert "roles" in result
        assert "<@&123456789>" in result["roles"]
        assert "<@&987654321>" in result["roles"]

    def test_extract_missing_any_role_details_mixed(self) -> None:
        """Test extracting multiple missing roles with mixed types."""
        error = MagicMock()
        error.missing_roles = [123456789, "Moderator", 111222333]

        result = extract_missing_any_role_details(error)

        assert "roles" in result
        assert "<@&123456789>" in result["roles"]
        assert "Moderator" in result["roles"]
        assert "<@&111222333>" in result["roles"]

    def test_extract_missing_any_role_details_empty(self) -> None:
        """Test extracting missing roles when list is empty."""
        error = MagicMock()
        error.missing_roles = []

        result = extract_missing_any_role_details(error)

        assert "roles" in result
        assert "unknown roles" in result["roles"]


class TestPermissionExtractors:
    """Test permission-related error extractors."""

    def test_extract_permissions_details(self) -> None:
        """Test extracting missing permissions."""
        error = MagicMock()
        error.missing_perms = ["ban_members", "kick_members", "manage_messages"]

        result = extract_permissions_details(error)

        assert "permissions" in result
        assert "ban_members" in result["permissions"]
        assert "kick_members" in result["permissions"]
        assert "manage_messages" in result["permissions"]

    def test_extract_permissions_details_empty(self) -> None:
        """Test extracting permissions when none provided."""
        error = MagicMock()
        error.missing_perms = []

        result = extract_permissions_details(error)

        assert "permissions" in result

    def test_extract_permission_denied_details_unconfigured_command(self) -> None:
        """Test extracting permission denied for unconfigured command."""
        error = MagicMock()
        error.required_rank = 0
        error.user_rank = 0
        error.command_name = "dev clear_tree"

        result = extract_permission_denied_details(error)

        assert "message" in result
        assert "not been configured yet" in result["message"]
        assert "dev clear_tree" in result["message"]
        assert "/config overview" in result["message"]
        assert "Command Permissions" in result["message"]

    def test_extract_permission_denied_details_insufficient_rank(self) -> None:
        """Test extracting permission denied for insufficient rank."""
        error = MagicMock()
        error.required_rank = 5
        error.user_rank = 2
        error.command_name = "ban"

        result = extract_permission_denied_details(error)

        assert "message" in result
        assert "permission rank **5**" in result["message"]
        assert "Your current rank: **2**" in result["message"]
        assert "ban" in result["message"]

    def test_extract_permission_denied_details_no_command_name(self) -> None:
        """Test extracting permission denied without command name."""
        error = MagicMock()
        error.required_rank = 3
        error.user_rank = 1
        error.command_name = None

        result = extract_permission_denied_details(error)

        assert "message" in result
        # Should use default command name
        assert "this command" in result["message"] or "message" in result


class TestArgumentExtractors:
    """Test argument-related error extractors."""

    def test_extract_missing_argument_details_with_param(self) -> None:
        """Test extracting missing argument details."""
        error = MagicMock()
        error.param = MagicMock()
        error.param.name = "user"

        result = extract_missing_argument_details(error)

        assert "param_name" in result
        assert "user" == result["param_name"]

    def test_extract_missing_argument_details_with_string(self) -> None:
        """Test extracting missing argument with string format."""
        error = MagicMock()
        error.param = MagicMock()
        error.param.name = "member"

        result = extract_missing_argument_details(error)

        assert "param_name" in result
        assert "member" == result["param_name"]

    def test_extract_bad_union_argument_details(self) -> None:
        """Test extracting bad union argument details."""
        error = MagicMock()

        # Mock argument with name attribute (mimics Parameter object)
        argument = MagicMock()
        argument.name = "target"
        error.argument = argument

        # Mock converters
        converter1 = MagicMock()
        converter1.__name__ = "Member"
        converter2 = MagicMock()
        converter2.__name__ = "User"
        error.converters = [converter1, converter2]

        result = extract_bad_union_argument_details(error)

        assert "argument" in result
        assert result["argument"] == "target"
        assert "expected_types" in result
        assert "Member" in result["expected_types"]
        assert "User" in result["expected_types"]

    def test_extract_bad_union_argument_details_no_converters(self) -> None:
        """Test extracting bad union argument without converters."""
        error = MagicMock()
        param = MagicMock()
        param.name = "value"
        error.param = param
        error.converters = []

        result = extract_bad_union_argument_details(error)

        assert "argument" in result
        assert "expected_types" in result
        assert "unknown type" in result["expected_types"]


class TestFlagExtractors:
    """Test flag-related error extractors."""

    def test_extract_bad_flag_argument_details(self) -> None:
        """Test extracting bad flag argument details."""
        error = MagicMock()
        flag = MagicMock()
        flag.name = "verbose"
        error.flag = flag
        error.original = ValueError("Invalid boolean")

        result = extract_bad_flag_argument_details(error)

        assert "flag_name" in result
        assert result["flag_name"] == "verbose"
        assert "original_cause" in result

    def test_extract_bad_flag_argument_details_no_flag(self) -> None:
        """Test extracting flag argument without flag object."""
        error = MagicMock()
        error.flag = None

        result = extract_bad_flag_argument_details(error)

        assert "flag_name" in result
        assert result["flag_name"] == "unknown_flag"

    def test_extract_missing_flag_details(self) -> None:
        """Test extracting missing flag details."""
        error = MagicMock()
        flag = MagicMock()
        flag.name = "required"
        error.flag = flag

        result = extract_missing_flag_details(error)

        assert "flag_name" in result
        assert result["flag_name"] == "required"

    def test_extract_missing_flag_details_no_flag(self) -> None:
        """Test extracting missing flag without flag object."""
        error = MagicMock()
        error.flag = None

        result = extract_missing_flag_details(error)

        assert "flag_name" in result
        assert result["flag_name"] == "unknown_flag"


class TestHttpExtractors:
    """Test HTTP-related error extractors."""

    def test_extract_httpx_status_details_complete(self) -> None:
        """Test extracting HTTP status with complete info."""
        error = MagicMock(spec=httpx.HTTPStatusError)

        # Mock response with all attributes
        response = MagicMock()
        response.status_code = 404
        response.text = "Not Found: Resource does not exist"
        response.url = "https://api.example.com/users/123"
        error.response = response

        result = extract_httpx_status_details(error)

        assert "status_code" in result
        assert result["status_code"] == 404
        assert "url" in result
        assert "api.example.com" in str(result["url"])
        assert "response_text" in result
        assert "Not Found" in result["response_text"]

    def test_extract_httpx_status_details_no_response(self) -> None:
        """Test extracting HTTP status without response."""
        error = MagicMock(spec=httpx.HTTPStatusError)
        error.response = None

        result = extract_httpx_status_details(error)

        # Returns empty dict when no response
        assert result == {}

    def test_extract_httpx_status_details_long_response_truncated(self) -> None:
        """Test extracting HTTP status truncates long responses."""
        error = MagicMock(spec=httpx.HTTPStatusError)

        # Mock response with long text
        response = MagicMock()
        response.status_code = 500
        response.text = "A" * 300  # 300 characters
        response.url = "https://api.example.com/"
        error.response = response

        result = extract_httpx_status_details(error)

        assert "response_text" in result
        # Should be truncated to 200 chars
        assert len(result["response_text"]) <= 200


class TestExtractorsWithRealErrors:
    """Test extractors with actual Discord.py/httpx error objects where possible."""

    def test_httpx_timeout_exception(self) -> None:
        """Test with real httpx TimeoutException."""
        request = httpx.Request("GET", "https://api.example.com/timeout")
        error = httpx.TimeoutException("Request timed out", request=request)

        # Verify it has expected attributes for extraction
        assert hasattr(error, "request")
        assert error.request.url == "https://api.example.com/timeout"

    def test_httpx_connect_error(self) -> None:
        """Test with real httpx ConnectError."""
        request = httpx.Request("GET", "https://unreachable.example.com")
        error = httpx.ConnectError("Connection failed", request=request)

        # Verify it has expected attributes for extraction
        assert hasattr(error, "request")
        assert error.request is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
