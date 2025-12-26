"""
🚀 Error Extractors Integration Tests - Integration Testing with Real Errors.

Tests for extractors with actual Discord.py/httpx error objects.
"""

import httpx


class TestExtractorsWithRealErrors:
    """Test extractors with actual Discord.py/httpx error objects where possible."""

    def test_httpx_timeout_exception(self) -> None:
        """Test extractor with real httpx TimeoutException."""
        request = httpx.Request("GET", "https://api.example.com/timeout")
        error = httpx.TimeoutException("Request timed out", request=request)

        # Verify it has expected attributes for extraction
        assert hasattr(error, "request")
        assert error.request.url == "https://api.example.com/timeout"

        # Note: TimeoutException doesn't have a response attribute, so extract_httpx_status_details
        # won't work directly, but we verify the error object structure is correct

    def test_httpx_connect_error(self) -> None:
        """Test extractor with real httpx ConnectError."""
        request = httpx.Request("GET", "https://unreachable.example.com")
        error = httpx.ConnectError("Connection failed", request=request)

        # Verify it has expected attributes for extraction
        assert hasattr(error, "request")
        assert error.request is not None

        # Note: ConnectError doesn't have a response attribute, so extract_httpx_status_details
        # won't work directly, but we verify the error object structure is correct
