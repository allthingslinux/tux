"""Tests for module HTTP integrations with centralized client."""

import asyncio
from unittest.mock import MagicMock

import httpx
import pytest

from tux.modules.utility.wiki import Wiki
from tux.services.http_client import http_client


class TestAvatarModuleHTTP:
    """Test avatar module HTTP functionality."""

    @pytest.mark.asyncio
    async def test_avatar_image_fetch(self, httpx_mock) -> None:
        """Test fetching avatar image data."""
        # Mock image data
        fake_image = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        httpx_mock.add_response(
            content=fake_image,
            headers={"Content-Type": "image/png"},
        )

        response = await http_client.get("https://cdn.discord.com/avatar.png")

        assert response.content == fake_image
        assert response.headers["Content-Type"] == "image/png"

        request = httpx_mock.get_request()
        assert "discord.com" in str(request.url)

    @pytest.mark.asyncio
    async def test_avatar_different_formats(self, httpx_mock) -> None:
        """Test different image format handling."""
        formats = [
            ("image/jpeg", b"\xff\xd8\xff"),
            ("image/png", b"\x89PNG"),
            ("image/gif", b"GIF89a"),
            ("image/webp", b"RIFF"),
        ]

        for content_type, magic_bytes in formats:
            httpx_mock.add_response(
                content=magic_bytes + b"fake_data",
                headers={"Content-Type": content_type},
            )

            response = await http_client.get(
                f"https://example.com/avatar.{content_type.split('/')[1]}",
            )
            assert response.headers["Content-Type"] == content_type
            assert response.content.startswith(magic_bytes)


class TestWikiModuleHTTP:
    """Test wiki module HTTP functionality."""

    @pytest.mark.asyncio
    async def test_arch_wiki_api_call(self, httpx_mock) -> None:
        """Test Arch Wiki API integration."""
        mock_response = {
            "query": {
                "search": [
                    {
                        "title": "Installation guide",
                        "snippet": "This document is a guide for installing Arch Linux...",
                    },
                ],
            },
        }
        httpx_mock.add_response(json=mock_response)

        bot = MagicMock()
        wiki = Wiki(bot)

        result = await wiki.query_wiki(wiki.arch_wiki_api_url, "installation")

        assert result[0] == "Installation guide"
        assert "wiki.archlinux.org" in result[1]

        request = httpx_mock.get_request()
        assert "wiki.archlinux.org" in str(request.url)
        assert "Installation" in str(request.url)

    @pytest.mark.asyncio
    async def test_atl_wiki_api_call(self, httpx_mock) -> None:
        """Test ATL Wiki API integration."""
        mock_response = {
            "query": {
                "search": [
                    {
                        "title": "Linux basics",
                        "snippet": "Basic Linux commands and concepts...",
                    },
                ],
            },
        }
        httpx_mock.add_response(json=mock_response)

        bot = MagicMock()
        wiki = Wiki(bot)

        result = await wiki.query_wiki(wiki.atl_wiki_api_url, "basics")

        assert result[0] == "Linux basics"
        assert "atl.wiki" in result[1]

    @pytest.mark.asyncio
    async def test_wiki_no_results(self, httpx_mock) -> None:
        """Test wiki API with no search results."""
        mock_response = {"query": {"search": []}}
        httpx_mock.add_response(json=mock_response)

        bot = MagicMock()
        wiki = Wiki(bot)

        result = await wiki.query_wiki(wiki.arch_wiki_api_url, "nonexistent")

        assert result[0] == "error"


class TestImageEffectModuleHTTP:
    """Test image effect module HTTP functionality."""

    @pytest.mark.asyncio
    async def test_fetch_image_for_processing(self, httpx_mock) -> None:
        """Test fetching images for effect processing."""
        # Create a minimal valid PNG
        fake_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10"
            b"\x08\x02\x00\x00\x00\x90\x91h6\x00\x00\x00\x19tEXtSoftware\x00Adobe"
            b" ImageReadyq\xc9e<\x00\x00\x00\x0eIDATx\x9cc\xf8\x0f\x00\x00\x01"
            b"\x00\x01\x00\x00\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        httpx_mock.add_response(content=fake_png)

        response = await http_client.get("https://example.com/test.png")

        assert response.content == fake_png
        assert len(response.content) > 0

    @pytest.mark.asyncio
    async def test_image_fetch_error_handling(self, httpx_mock) -> None:
        """Test error handling when fetching images."""
        httpx_mock.add_response(status_code=404)

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await http_client.get("https://example.com/missing.png")

        assert exc_info.value.response.status_code == 404


class TestMailModuleHTTP:
    """Test mail module HTTP functionality."""

    @pytest.mark.asyncio
    async def test_mailcow_api_call(self, httpx_mock) -> None:
        """Test Mailcow API integration."""
        mock_response = [{"type": "success", "msg": "Mailbox created"}]
        httpx_mock.add_response(json=mock_response)

        # Simulate the mail module API call
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-API-Key": "test-key",
            "Authorization": "Bearer test-key",
        }

        response = await http_client.post(
            "https://mail.example.com/api/v1/add/mailbox",
            headers=headers,
            json={"local": "testuser", "domain": "example.com"},
            timeout=10.0,
        )

        assert response.json() == mock_response

        request = httpx_mock.get_request()
        assert request.headers["X-API-Key"] == "test-key"
        assert request.headers["Authorization"] == "Bearer test-key"

    @pytest.mark.asyncio
    async def test_mailcow_api_error(self, httpx_mock) -> None:
        """Test Mailcow API error handling."""
        httpx_mock.add_response(
            status_code=400,
            json={"type": "error", "msg": "Invalid domain"},
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            await http_client.post(
                "https://mail.example.com/api/v1/add/mailbox",
                json={"local": "testuser", "domain": "invalid"},
                timeout=10.0,
            )

        assert exc_info.value.response.status_code == 400
        assert exc_info.value.response.json()["type"] == "error"


class TestHTTPClientPerformance:
    """Test HTTP client performance characteristics."""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, httpx_mock) -> None:
        """Test handling multiple concurrent requests."""
        # Add multiple responses
        for i in range(10):
            httpx_mock.add_response(json={"request": i})

        # Make concurrent requests
        tasks = [
            http_client.get(f"https://api.example.com/endpoint/{i}") for i in range(10)
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 10
        for response in responses:
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_connection_reuse(self, httpx_mock) -> None:
        """Test that connections are reused (indirectly)."""
        # Add multiple responses for the same host
        for _ in range(5):
            httpx_mock.add_response(json={"status": "ok"})

        # Make multiple requests to the same host
        for _ in range(5):
            response = await http_client.get("https://api.example.com/test")
            assert response.status_code == 200

        # All requests should have been handled
        requests = httpx_mock.get_requests()
        assert len(requests) == 5

        # All requests should be to the same host
        for request in requests:
            assert "api.example.com" in str(request.url)
