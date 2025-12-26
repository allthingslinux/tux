"""
🚀 Error Extractors Role Tests - Role-Related Error Extractors.

Tests for role-related error extractors.
"""

from unittest.mock import MagicMock

from tux.services.handlers.error.extractors import (
    extract_missing_any_role_details,
    extract_missing_role_details,
)


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
