"""Unit tests for db health cache check (_check_cache)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure project root is on path so scripts.db.health can be imported
_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scripts.db.health import _check_cache


@pytest.mark.unit
class TestCheckCache:
    """_check_cache returns skipped/healthy/unhealthy as expected."""

    @pytest.mark.asyncio
    async def test_returns_skipped_when_valkey_url_empty(self) -> None:
        """When CONFIG.valkey_url is empty, status is skipped."""
        with patch("scripts.db.health.CONFIG") as mock_config:
            mock_config.valkey_url = None
            result = await _check_cache()
        assert result["status"] == "skipped"
        assert "not configured" in result.get("message", "").lower()

    @pytest.mark.asyncio
    async def test_returns_skipped_when_valkey_url_empty_string(self) -> None:
        """When CONFIG.valkey_url is '', status is skipped."""
        with patch("scripts.db.health.CONFIG") as mock_config:
            mock_config.valkey_url = ""
            result = await _check_cache()
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_returns_healthy_when_connect_and_ping_ok(self) -> None:
        """When Valkey URL is set and connect + ping succeed, status is healthy."""
        fake_client = MagicMock()
        fake_client.ping = AsyncMock(return_value=True)
        fake_client.aclose = AsyncMock()
        mock_config = MagicMock()
        mock_config.valkey_url = "valkey://localhost:6379/0"
        with (
            patch("scripts.db.health.CONFIG", mock_config),
            patch("tux.cache.service.CONFIG", mock_config),
            patch("tux.cache.service.Valkey") as mock_valkey,
        ):
            mock_valkey.from_url.return_value = fake_client
            result = await _check_cache()
        assert result["status"] == "healthy"
        assert (
            "ping" in result.get("message", "").lower()
            or "ok" in result.get("message", "").lower()
        )
        fake_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_unhealthy_when_ping_fails(self) -> None:
        """When connect succeeds but ping raises, status is unhealthy."""
        fake_client = MagicMock()
        fake_client.ping = AsyncMock(side_effect=ConnectionError("ping failed"))
        fake_client.aclose = AsyncMock()
        mock_config = MagicMock()
        mock_config.valkey_url = "valkey://localhost:6379/0"
        with (
            patch("scripts.db.health.CONFIG", mock_config),
            patch("tux.cache.service.CONFIG", mock_config),
            patch("tux.cache.service.Valkey") as mock_valkey,
        ):
            mock_valkey.from_url.return_value = fake_client
            result = await _check_cache()
        assert result["status"] == "unhealthy"
        assert "ping" in result.get("message", "").lower()
        fake_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_unhealthy_when_connect_raises(self) -> None:
        """When connect raises, status is unhealthy and message contains error."""
        mock_config = MagicMock()
        mock_config.valkey_url = "valkey://localhost:6379/0"
        with (
            patch("scripts.db.health.CONFIG", mock_config),
            patch("tux.cache.service.CONFIG", mock_config),
            patch("tux.cache.service.Valkey") as mock_valkey,
        ):
            mock_valkey.from_url.side_effect = ConnectionError("Connection refused")
            result = await _check_cache()
        assert result["status"] == "unhealthy"
        assert "Connection refused" in result.get("message", "")
