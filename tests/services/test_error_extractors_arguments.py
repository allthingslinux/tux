"""
🚀 Error Extractors Argument Tests - Argument-Related Error Extractors.

Tests for argument-related error extractors.
"""

from unittest.mock import MagicMock

from tux.services.handlers.error.extractors import (
    extract_bad_union_argument_details,
    extract_missing_argument_details,
)


class TestArgumentExtractors:
    """Test argument-related error extractors."""

    def test_extract_missing_argument_details_with_param(self) -> None:
        """Test extracting missing argument details."""
        error = MagicMock()
        error.param = MagicMock()
        error.param.name = "user"

        result = extract_missing_argument_details(error)

        assert "param_name" in result
        assert result["param_name"] == "user"

    def test_extract_missing_argument_details_with_string(self) -> None:
        """Test extracting missing argument with string format."""
        error = MagicMock()
        error.param = MagicMock()
        error.param.name = "member"

        result = extract_missing_argument_details(error)

        assert "param_name" in result
        assert result["param_name"] == "member"

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
