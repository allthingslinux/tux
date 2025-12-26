"""
🚀 Error Extractors Flag Tests - Flag-Related Error Extractors.

Tests for flag-related error extractors.
"""

from unittest.mock import MagicMock

from tux.services.handlers.error.extractors import (
    extract_bad_flag_argument_details,
    extract_missing_flag_details,
)


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
