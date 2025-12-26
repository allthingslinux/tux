"""
🚀 Error Extractors Utility Tests - Utility Function Testing.

Tests for utility functions used by error extractors.
"""

from unittest.mock import MagicMock

from tux.services.handlers.error.extractors import (
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
