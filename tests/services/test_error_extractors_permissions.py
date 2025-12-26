"""
🚀 Error Extractors Permission Tests - Permission-Related Error Extractors.

Tests for permission-related error extractors.
"""

from unittest.mock import MagicMock

from tux.services.handlers.error.extractors import (
    extract_permission_denied_details,
    extract_permissions_details,
)


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
        assert "configure command permissions" in result["message"]

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
