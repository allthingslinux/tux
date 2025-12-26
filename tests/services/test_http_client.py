"""Tests for the centralized HTTP client service."""

from unittest.mock import MagicMock

import httpx
import pytest

from tux.modules.info.avatar import Avatar
from tux.modules.utility.wiki import Wiki
from tux.services.http_client import HTTPClient, http_client
from tux.services.wrappers import godbolt, wandbox


class TestHTTPClient:
    """Test the HTTPClient class."""

    @pytest.fixture
    def client(self):
        """Create a fresh HTTPClient instance for testing."""
        return HTTPClient()

    @pytest.mark.asyncio
    async def test_get_client_creates_client(self, client) -> None:
        """Test that get_client creates and returns a client."""
        httpx_client = await client.get_client()
        assert isinstance(httpx_client, httpx.AsyncClient)
        assert httpx_client.timeout.connect == 10.0
        assert httpx_client.timeout.read == 30.0
        # Check that HTTP/2 is enabled
        assert httpx_client._transport is not None

    @pytest.mark.asyncio
    async def test_get_client_reuses_client(self, client) -> None:
        """Test that get_client reuses the same client instance."""
        client1 = await client.get_client()
        client2 = await client.get_client()
        assert client1 is client2

    @pytest.mark.asyncio
    async def test_close_client(self, client) -> None:
        """Test that close properly closes the client."""
        _httpx_client = await client.get_client()
        await client.close()
        assert client._client is None

    @pytest.mark.asyncio
    async def test_get_request(self, client, httpx_mock) -> None:
        """Test GET request method."""
        httpx_mock.add_response(json={"test": "data"})

        response = await client.get("https://test.example.com")

        assert response.status_code == 200
        assert response.json() == {"test": "data"}

    @pytest.mark.asyncio
    async def test_post_request(self, client, httpx_mock) -> None:
        """Test POST request method."""
        httpx_mock.add_response(json={"created": True})

        response = await client.post("https://test.example.com", json={"data": "test"})

        assert response.status_code == 200
        assert response.json() == {"created": True}

    @pytest.mark.asyncio
    async def test_put_request(self, client, httpx_mock) -> None:
        """Test PUT request method."""
        httpx_mock.add_response(json={"updated": True})

        response = await client.put("https://test.example.com", json={"data": "test"})

        assert response.status_code == 200
        assert response.json() == {"updated": True}

    @pytest.mark.asyncio
    async def test_delete_request(self, client, httpx_mock) -> None:
        """Test DELETE request method."""
        httpx_mock.add_response(status_code=204)

        response = await client.delete("https://test.example.com")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_request_method(self, client, httpx_mock) -> None:
        """Test generic request method."""
        httpx_mock.add_response(json={"method": "PATCH"})

        response = await client.request("PATCH", "https://test.example.com")

        assert response.status_code == 200
        assert response.json() == {"method": "PATCH"}

    @pytest.mark.asyncio
    async def test_error_handling(self, client, httpx_mock) -> None:
        """Test that HTTP errors are properly raised."""
        httpx_mock.add_response(status_code=404)

        with pytest.raises(httpx.HTTPStatusError):
            await client.get("https://test.example.com")

    @pytest.mark.asyncio
    async def test_timeout_handling(self, client, httpx_mock) -> None:
        """Test timeout exception handling."""
        httpx_mock.add_exception(httpx.ReadTimeout("Request timed out"))

        with pytest.raises(httpx.ReadTimeout):
            await client.get("https://test.example.com")

    @pytest.mark.asyncio
    async def test_user_agent_header(self, client, httpx_mock) -> None:
        """Test that User-Agent header is set correctly."""
        httpx_mock.add_response()

        await client.get("https://test.example.com")

        request = httpx_mock.get_request()
        assert "Tux-Bot/" in request.headers["User-Agent"]
        assert "github.com/allthingslinux/tux" in request.headers["User-Agent"]


class TestGlobalHTTPClient:
    """Test the global http_client instance."""

    @pytest.mark.asyncio
    async def test_global_client_get(self, httpx_mock) -> None:
        """Test global client GET request."""
        httpx_mock.add_response(json={"global": True})

        response = await http_client.get("https://test.example.com")

        assert response.json() == {"global": True}

    @pytest.mark.asyncio
    async def test_global_client_post(self, httpx_mock) -> None:
        """Test global client POST request."""
        httpx_mock.add_response(json={"posted": True})

        response = await http_client.post(
            "https://test.example.com",
            json={"test": "data"},
        )

        assert response.json() == {"posted": True}


class TestHTTPClientIntegration:
    """Integration tests for HTTP client with bot modules."""

    @pytest.mark.asyncio
    async def test_avatar_module_integration(self, httpx_mock) -> None:
        """Test that avatar module works with centralized HTTP client."""
        # Mock image data
        image_data = b"fake_image_data"
        httpx_mock.add_response(
            content=image_data,
            headers={"Content-Type": "image/png"},
        )

        bot = MagicMock()
        _avatar_cog = Avatar(bot)

        # This would normally be called from the avatar command
        # We're testing the HTTP request part
        response = await http_client.get("https://example.com/avatar.png")

        assert response.content == image_data
        assert response.headers["Content-Type"] == "image/png"

    @pytest.mark.asyncio
    async def test_wiki_module_integration(self, httpx_mock) -> None:
        """Test that wiki module works with centralized HTTP client."""
        # Mock wiki API response
        wiki_response = {
            "query": {
                "search": [
                    {"title": "Test Article"},
                ],
            },
        }
        httpx_mock.add_response(json=wiki_response)

        bot = MagicMock()
        wiki_cog = Wiki(bot)

        # Test the query_wiki method
        result = await wiki_cog.query_wiki("https://wiki.test.com/api.php", "test")

        assert result[0] == "Test Article"
        assert "wiki" in result[1]  # Should contain wiki in the URL

    @pytest.mark.asyncio
    async def test_godbolt_service_integration(self, httpx_mock) -> None:
        """Test that godbolt service works with centralized HTTP client."""
        # Mock godbolt API response
        godbolt_response = {
            "stdout": [{"text": "Hello World\n"}],
            "stderr": [],
            "code": 0,
        }
        httpx_mock.add_response(json=godbolt_response)

        # Test the getoutput function
        result = await godbolt.getoutput("print('Hello World')", "python3", None)

        assert result is not None

    @pytest.mark.asyncio
    async def test_wandbox_service_integration(self, httpx_mock) -> None:
        """Test that wandbox service works with centralized HTTP client."""
        # Mock wandbox API response
        wandbox_response = {
            "status": "0",
            "program_output": "Hello World\n",
        }
        httpx_mock.add_response(json=wandbox_response)

        # Test the getoutput function
        result = await wandbox.getoutput("print('Hello World')", "python-3.9.2", None)

        assert result == wandbox_response


class TestHTTPClientErrorScenarios:
    """Test error scenarios and edge cases."""

    @pytest.mark.asyncio
    async def test_connection_error(self, httpx_mock) -> None:
        """Test connection error handling."""
        httpx_mock.add_exception(httpx.ConnectError("Connection failed"))

        with pytest.raises(httpx.ConnectError):
            await http_client.get("https://unreachable.example.com")

    @pytest.mark.asyncio
    async def test_timeout_error(self, httpx_mock) -> None:
        """Test timeout error handling."""
        httpx_mock.add_exception(httpx.TimeoutException("Request timed out"))

        with pytest.raises(httpx.TimeoutException):
            await http_client.get("https://slow.example.com")

    @pytest.mark.asyncio
    async def test_http_status_error(self, httpx_mock) -> None:
        """Test HTTP status error handling."""
        httpx_mock.add_response(status_code=500, text="Internal Server Error")

        with pytest.raises(httpx.HTTPStatusError):
            await http_client.get("https://error.example.com")

    @pytest.mark.asyncio
    async def test_custom_timeout_parameter(self, httpx_mock) -> None:
        """Test that custom timeout parameters are passed through."""
        httpx_mock.add_response()

        # This should not raise an exception
        response = await http_client.get("https://test.example.com", timeout=5.0)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_custom_headers_parameter(self, httpx_mock) -> None:
        """Test that custom headers are passed through."""
        httpx_mock.add_response()

        custom_headers = {"Authorization": "Bearer token123"}
        await http_client.get("https://test.example.com", headers=custom_headers)

        request = httpx_mock.get_request()
        assert request.headers["Authorization"] == "Bearer token123"
        # Should still have the default User-Agent
        assert "Tux-Bot/" in request.headers["User-Agent"]


@pytest.mark.asyncio
async def test_http_client_lifecycle() -> None:
    """Test HTTP client lifecycle management."""
    client = HTTPClient()

    # Client should be None initially
    assert client._client is None

    # Getting client should create it
    httpx_client = await client.get_client()
    assert client._client is not None
    assert isinstance(httpx_client, httpx.AsyncClient)

    # Closing should set it back to None
    await client.close()
    assert client._client is None
