"""
🚀 Error Extractors Integration Tests - Integration Testing with Real Errors.

Tests for extractors with actual Discord.py/httpx error objects.
"""

import httpx

from tux.services.handlers.error.extractors import extract_httpx_status_details


class TestExtractorsWithRealErrors:
    """Test extractors with actual Discord.py/httpx error objects where possible."""

    def test_httpx_timeout_exception(self) -> None:
        """Test extractor with real httpx TimeoutException."""
        request = httpx.Request("GET", "https://api.example.com/timeout")
        error = httpx.TimeoutException("Request timed out", request=request)

        # Verify it has expected attributes for extraction
        assert hasattr(error, "request")
        assert error.request.url == "https://api.example.com/timeout"

        # Test that extractor handles TimeoutException gracefully
        # (returns empty dict since it doesn't have a response attribute)
        context = extract_httpx_status_details(error)
        assert context == {}  # TimeoutException has no response, so returns empty dict

    def test_httpx_connect_error(self) -> None:
        """Test extractor with real httpx ConnectError."""
        request = httpx.Request("GET", "https://unreachable.example.com")
        error = httpx.ConnectError("Connection failed", request=request)

        # Verify it has expected attributes for extraction
        assert hasattr(error, "request")
        assert error.request is not None

        # Test that extractor handles ConnectError gracefully
        # (returns empty dict since it doesn't have a response attribute)
        context = extract_httpx_status_details(error)
        assert context == {}  # ConnectError has no response, so returns empty dict

    def test_httpx_status_error(self) -> None:
        """Test extractor with real httpx HTTPStatusError."""
        request = httpx.Request("GET", "https://api.example.com/not-found")
        # Create a mock response for HTTPStatusError
        response = httpx.Response(
            404,
            request=request,
            text="Not Found: Resource does not exist",
        )
        error = httpx.HTTPStatusError("Not Found", request=request, response=response)

        # Test that extractor extracts details from HTTPStatusError
        context = extract_httpx_status_details(error)

        assert "status_code" in context
        assert context["status_code"] == 404
        assert "url" in context
        assert context["url"] == "https://api.example.com/not-found"
        assert "response_text" in context
        assert "Not Found" in context["response_text"]
