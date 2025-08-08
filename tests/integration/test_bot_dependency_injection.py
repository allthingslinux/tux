"""Integration tests for bot startup with dependency injection.

This module contains integration tests that verify the bot properly initializes
the dependency injection container during startup and makes it available to cogs.
"""

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest
from discord.ext import commands

from tux.core.bot import ContainerInitializationError, Tux
from tux.core.container import ServiceContainer
from tux.core.interfaces import IBotService, IConfigService, IDatabaseService
from tux.core.service_registry import ServiceRegistry


class TestBotDependencyInjectionIntegration:
    """Integration tests for bot dependency injection system."""

    @pytest.fixture
    async def mock_bot(self):
        """Create a mock bot instance for testing."""
        # Mock the database connection
        with patch("tux.bot.db") as mock_db:
            mock_db.connect = AsyncMock()
            mock_db.is_connected.return_value = True
            mock_db.is_registered.return_value = True
            mock_db.disconnect = AsyncMock()

            # Mock CogLoader to prevent actual cog loading
            with patch("tux.bot.CogLoader.setup", new_callable=AsyncMock):
                # Create bot with minimal intents for testing
                intents = discord.Intents.default()
                bot = Tux(command_prefix="!", intents=intents)

                # Cancel the setup task to prevent automatic setup
                if bot.setup_task:
                    bot.setup_task.cancel()
                    try:
                        await bot.setup_task
                    except asyncio.CancelledError:
                        pass

                yield bot

                # Cleanup
                if not bot.is_closed():
                    await bot.close()

    @pytest.mark.asyncio
    async def test_bot_initializes_container_during_setup(self, mock_bot):
        """Test that the bot initializes the dependency injection container during setup."""
        # Ensure container is not initialized before setup
        assert mock_bot.container is None

        # Run setup manually
        await mock_bot.setup()

        # Verify container is initialized
        assert mock_bot.container is not None
        assert isinstance(mock_bot.container, ServiceContainer)

    @pytest.mark.asyncio
    async def test_container_has_required_services_registered(self, mock_bot):
        """Test that the container has all required services registered after setup."""
        await mock_bot.setup()

        # Verify all required services are registered
        assert mock_bot.container.is_registered(IDatabaseService)
        assert mock_bot.container.is_registered(IConfigService)
        assert mock_bot.container.is_registered(IBotService)

    @pytest.mark.asyncio
    async def test_container_services_can_be_resolved(self, mock_bot):
        """Test that services can be successfully resolved from the container."""
        await mock_bot.setup()

        # Test service resolution
        db_service = mock_bot.container.get(IDatabaseService)
        config_service = mock_bot.container.get(IConfigService)
        bot_service = mock_bot.container.get(IBotService)

        assert db_service is not None
        assert config_service is not None
        assert bot_service is not None

    @pytest.mark.asyncio
    async def test_container_initialization_failure_handling(self, mock_bot):
        """Test that container initialization failures are properly handled."""
        # Mock ServiceRegistry to raise an exception
        with patch.object(ServiceRegistry, 'configure_container', side_effect=Exception("Test error")):
            with pytest.raises(ContainerInitializationError):
                await mock_bot.setup()

    @pytest.mark.asyncio
    async def test_container_validation_failure_handling(self, mock_bot):
        """Test that container validation failures are properly handled."""
        # Mock ServiceRegistry validation to fail
        with patch.object(ServiceRegistry, 'validate_container', return_value=False):
            with pytest.raises(ContainerInitializationError):
                await mock_bot.setup()

    @pytest.mark.asyncio
    async def test_setup_callback_handles_container_success(self, mock_bot):
        """Test that the setup callback properly handles successful container initialization."""
        # Run setup
        await mock_bot.setup()

        # Verify setup completed successfully
        assert mock_bot.setup_complete is True
        assert mock_bot.container is not None

    @pytest.mark.asyncio
    async def test_setup_callback_handles_container_failure(self, mock_bot):
        """Test that the setup callback properly handles container initialization failure."""
        # Mock container setup to fail
        with patch.object(mock_bot, '_setup_container', side_effect=ContainerInitializationError("Test error")):
            with pytest.raises(ContainerInitializationError):
                await mock_bot.setup()

    @pytest.mark.asyncio
    async def test_container_cleanup_during_shutdown(self, mock_bot):
        """Test that the container is properly cleaned up during bot shutdown."""
        # Setup the bot first
        await mock_bot.setup()
        assert mock_bot.container is not None

        # Shutdown the bot
        await mock_bot.shutdown()

        # Verify container is cleaned up
        assert mock_bot.container is None

    @pytest.mark.asyncio
    async def test_container_available_before_cog_loading(self, mock_bot):
        """Test that the container is available before cogs are loaded."""
        cog_loader_called = False
        original_container = None

        async def mock_cog_setup(bot):
            nonlocal cog_loader_called, original_container
            cog_loader_called = True
            original_container = bot.container
            # Verify container is available when cogs are being loaded
            assert bot.container is not None
            assert isinstance(bot.container, ServiceContainer)

        with patch("tux.bot.CogLoader.setup", side_effect=mock_cog_setup):
            await mock_bot.setup()

        # Verify the mock was called and container was available
        assert cog_loader_called
        assert original_container is not None

    @pytest.mark.asyncio
    async def test_setup_order_database_then_container_then_cogs(self, mock_bot):
        """Test that setup follows the correct order: database, container, then cogs."""
        setup_order = []

        # Mock methods to track call order
        original_setup_database = mock_bot._setup_database
        original_setup_container = mock_bot._setup_container
        original_load_cogs = mock_bot._load_cogs

        async def track_setup_database():
            setup_order.append("database")
            await original_setup_database()

        async def track_setup_container():
            setup_order.append("container")
            await original_setup_container()

        async def track_load_cogs():
            setup_order.append("cogs")
            await original_load_cogs()

        mock_bot._setup_database = track_setup_database
        mock_bot._setup_container = track_setup_container
        mock_bot._load_cogs = track_load_cogs

        await mock_bot.setup()

        # Verify correct order
        assert setup_order == ["database", "container", "cogs"]

    @pytest.mark.asyncio
    async def test_container_logging_during_initialization(self, mock_bot, caplog):
        """Test that proper logging occurs during container initialization."""
        await mock_bot.setup()

        # Check for expected log messages
        log_messages = [record.message for record in caplog.records]

        # Should have container initialization messages
        assert any("Initializing dependency injection container" in msg for msg in log_messages)
        assert any("Container initialized with services" in msg for msg in log_messages)

    @pytest.mark.asyncio
    async def test_fallback_behavior_when_container_unavailable(self):
        """Test that the system can handle cases where container is not available."""
        # Create a bot without going through normal setup
        intents = discord.Intents.default()
        bot = Tux(command_prefix="!", intents=intents)

        # Cancel setup task
        if bot.setup_task:
            bot.setup_task.cancel()
            try:
                await bot.setup_task
            except asyncio.CancelledError:
                pass

        # Verify container is None (fallback scenario)
        assert bot.container is None

        # The bot should still be functional for basic operations
        assert hasattr(bot, 'container')

        # Cleanup
        if not bot.is_closed():
            await bot.close()
