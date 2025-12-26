"""
🚀 Error Extractors HTTP Tests - HTTP-Related Error Extractors.

Tests for HTTP-related error extractors.
"""

from unittest.mock import MagicMock

import httpx

from tux.services.handlers.error.extractors import extract_httpx_status_details


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
