"""Comprehensive integration tests for the dependency injection system.

This module contains integration tests that verify the complete dependency injection
system works correctly in real-world scenarios, including bot startup, service
registration, cog loading, and end-to-end functionality.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch

import discord
import pytest
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.base_cog import BaseCog
from tux.core.container import ServiceContainer
from tux.core.interfaces import IBotService, IConfigService, IDatabaseService
from tux.core.service_registry import ServiceRegistry
from tux.core.services import BotService, ConfigService, DatabaseService
from tests.fixtures.dependency_injection import (
    PerformanceTimer,
    assert_service_resolution_performance,
    create_test_container_with_real_services,
    measure_service_resolution_performance,
)


class TestCogForIntegration(BaseCog):
    """Test cog for integration testing with dependency injection."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the test cog."""
        super().__init__(bot)
        self.initialization_successful = True
        self.services_available = {
            "database": self.db_service is not None,
            "bot": self.bot_service is not None,
            "config": self.config_service is not None,
        }

    @commands.command(name="test_services")
    async def test_services_command(self, ctx: commands.Context) -> None:
        """Test command that uses all injected services."""
        try:
            # Test database service
            controller = self.db_service.get_controller()
            db_result = await self.db_service.execute_query("test_operation", ctx.author.id)

            # Test bot service
            latency = self.bot_service.latency
            bot_user = self.bot_service.user

            # Test config service
            dev_mode = self.config_service.is_dev_mode()

            await ctx.send(
                f"Services working! DB: {db_result is not None}, "
                f"Latency: {latency:.3f}s, Dev: {dev_mode}",
            )
        except Exception as e:
            await ctx.send(f"Service error: {e}")

    async def get_service_health(self) -> dict:
        """Get health status of all services."""
        health = {}

        try:
            # Test database service
            controller = self.db_service.get_controller()
            health["database"] = controller is not None
        except Exception:
            health["database"] = False

        try:
            # Test bot service
            latency = self.bot_service.latency
            health["bot"] = latency is not None
        except Exception:
            health["bot"] = False

        try:
            # Test config service
            dev_mode = self.config_service.is_dev_mode()
            health["config"] = isinstance(dev_mode, bool)
        except Exception:
            health["config"] = False

        return health


class TestDependencyInjectionIntegration:
    """Comprehensive integration tests for dependency injection system."""

    @pytest.fixture
    async def integration_bot(self):
        """Create a bot instance for integration testing."""
        # Mock the database connection
        with patch("tux.bot.db") as mock_db:
            mock_db.connect = AsyncMock()
            mock_db.is_connected.return_value = True
            mock_db.is_registered.return_value = True
            mock_db.disconnect = AsyncMock()

            # Mock CogLoader to prevent loading all cogs
            with patch("tux.bot.CogLoader.setup", new_callable=AsyncMock):
                # Create bot with minimal intents
                intents = discord.Intents.default()
                bot = Tux(command_prefix="!", intents=intents)

                # Cancel the automatic setup task
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

    @pytest.fixture
    async def bot_with_test_cog(self, integration_bot):
        """Create a bot with the test cog loaded."""
        # Setup the bot first
        await integration_bot.setup()

        # Add the test cog
        await integration_bot.add_cog(TestCogForIntegration(integration_bot))

        return integration_bot

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_complete_bot_startup_with_container_initialization(self, integration_bot):
        """Test complete bot startup with container initialization."""
        # Verify initial state
        assert integration_bot.container is None
        assert not integration_bot.setup_complete

        # Perform setup
        start_time = time.perf_counter()
        await integration_bot.setup()
        setup_time = time.perf_counter() - start_time

        # Verify setup completed successfully
        assert integration_bot.setup_complete
        assert integration_bot.container is not None
        assert isinstance(integration_bot.container, ServiceContainer)

        # Verify setup time is reasonable (should be under 5 seconds)
        assert setup_time < 5.0, f"Bot setup took too long: {setup_time:.3f}s"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_service_registration_and_resolution_in_real_environment(self, integration_bot):
        """Test service registration and resolution in real environment."""
        await integration_bot.setup()
        container = integration_bot.container

        # Test that all required services are registered
        required_services = [IDatabaseService, IBotService, IConfigService]
        for service_type in required_services:
            assert container.is_registered(service_type), f"{service_type.__name__} not registered"

        # Test service resolution
        db_service = container.get(IDatabaseService)
        bot_service = container.get(IBotService)
        config_service = container.get(IConfigService)

        # Verify service types
        assert isinstance(db_service, DatabaseService)
        assert isinstance(bot_service, BotService)
        assert isinstance(config_service, ConfigService)

        # Test service functionality
        assert db_service.get_controller() is not None
        assert isinstance(bot_service.latency, float)
        assert isinstance(config_service.is_dev_mode(), bool)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cog_loading_with_dependency_injection(self, integration_bot):
        """Test cog loading with dependency injection."""
        await integration_bot.setup()

        # Load the test cog
        test_cog = TestCogForIntegration(integration_bot)
        await integration_bot.add_cog(test_cog)

        # Verify cog was loaded successfully
        assert integration_bot.get_cog("TestCogForIntegration") is not None

        # Verify dependency injection worked
        assert test_cog.initialization_successful
        assert all(test_cog.services_available.values()), f"Services not available: {test_cog.services_available}"

        # Verify services are the correct types
        assert isinstance(test_cog.db_service, DatabaseService)
        assert isinstance(test_cog.bot_service, BotService)
        assert isinstance(test_cog.config_service, ConfigService)

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_functionality_with_injected_services(self, bot_with_test_cog):
        """Test end-to-end functionality with injected services."""
        bot = bot_with_test_cog
        test_cog = bot.get_cog("TestCogForIntegration")

        # Test service health check
        health = await test_cog.get_service_health()
        assert all(health.values()), f"Service health check failed: {health}"

        # Test command execution (simulate)
        ctx = Mock(spec=commands.Context)
        ctx.author = Mock()
        ctx.author.id = 12345
        ctx.send = AsyncMock()

        # Mock database query to avoid actual database calls
        with patch.object(test_cog.db_service, 'execute_query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = {"test": "data"}

            await test_cog.test_services_command(ctx)

        # Verify command executed successfully
        ctx.send.assert_called_once()
        call_args = ctx.send.call_args[0][0]
        assert "Services working!" in call_args
        assert "DB: True" in call_args
        assert "Latency:" in call_args

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_service_singleton_behavior_across_cogs(self, integration_bot):
        """Test that singleton services are shared across multiple cogs."""
        await integration_bot.setup()

        # Create multiple test cogs
        cog1 = TestCogForIntegration(integration_bot)
        cog2 = TestCogForIntegration(integration_bot)

        await integration_bot.add_cog(cog1)
        await integration_bot.add_cog(cog2, override=True)  # Override name conflict

        # Verify that singleton services are the same instance
        assert cog1.db_service is cog2.db_service, "DatabaseService should be singleton"
        assert cog1.config_service is cog2.config_service, "ConfigService should be singleton"
        # BotService is registered as instance, so should also be the same
        assert cog1.bot_service is cog2.bot_service, "BotService should be singleton"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_performance_no_degradation_in_startup_time(self, integration_bot):
        """Test that dependency injection doesn't degrade bot startup performance."""
        # Measure startup time multiple times
        startup_times = []

        for _ in range(3):
            # Reset bot state
            integration_bot.container = None
            integration_bot.setup_complete = False

            # Measure startup time
            start_time = time.perf_counter()
            await integration_bot.setup()
            end_time = time.perf_counter()

            startup_times.append(end_time - start_time)

        # Calculate average startup time
        avg_startup_time = sum(startup_times) / len(startup_times)
        max_startup_time = max(startup_times)

        # Verify performance requirements
        assert avg_startup_time < 2.0, f"Average startup time too slow: {avg_startup_time:.3f}s"
        assert max_startup_time < 5.0, f"Maximum startup time too slow: {max_startup_time:.3f}s"

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_service_resolution_performance(self, integration_bot):
        """Test service resolution performance meets requirements."""
        await integration_bot.setup()
        container = integration_bot.container

        # Test performance for each service type
        service_types = [IDatabaseService, IBotService, IConfigService]

        for service_type in service_types:
            # Test first resolution (may be slower due to instantiation)
            with PerformanceTimer() as timer:
                service = container.get(service_type)
                assert service is not None

            first_resolution_time = timer.measurements[0]

            # Test subsequent resolutions (should be faster for singletons)
            assert_service_resolution_performance(
                container,
                service_type,
                max_average_time=0.001,  # 1ms
                iterations=100,
            )

            # Log performance for debugging
            print(f"{service_type.__name__} first resolution: {first_resolution_time:.6f}s")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_container_error_handling_in_real_environment(self, integration_bot):
        """Test container error handling in real environment."""
        await integration_bot.setup()
        container = integration_bot.container

        # Test resolution of unregistered service
        class UnregisteredService:
            pass

        with pytest.raises(Exception):  # Should raise ServiceResolutionError
            container.get(UnregisteredService)

        # Test optional resolution of unregistered service
        result = container.get_optional(UnregisteredService)
        assert result is None

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fallback_behavior_when_container_fails(self):
        """Test fallback behavior when container initialization fails."""
        # Mock ServiceRegistry to fail
        with patch.object(ServiceRegistry, 'configure_container', side_effect=Exception("Container setup failed")):
            with patch("tux.bot.db") as mock_db:
                mock_db.connect = AsyncMock()
                mock_db.is_connected.return_value = True
                mock_db.is_registered.return_value = True
                mock_db.disconnect = AsyncMock()

                intents = discord.Intents.default()
                bot = Tux(command_prefix="!", intents=intents)

                # Cancel automatic setup
                if bot.setup_task:
                    bot.setup_task.cancel()
                    try:
                        await bot.setup_task
                    except asyncio.CancelledError:
                        pass

                # Setup should fail with container initialization error
                with pytest.raises(Exception):  # ContainerInitializationError
                    await bot.setup()

                # Cleanup
                if not bot.is_closed():
                    await bot.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cog_fallback_when_container_unavailable(self):
        """Test that cogs can fall back when container is unavailable."""
        # Create bot without container
        with patch("tux.bot.db") as mock_db:
            mock_db.connect = AsyncMock()
            mock_db.is_connected.return_value = True
            mock_db.is_registered.return_value = True
            mock_db.disconnect = AsyncMock()

            intents = discord.Intents.default()
            bot = Tux(command_prefix="!", intents=intents)

            # Cancel automatic setup
            if bot.setup_task:
                bot.setup_task.cancel()
                try:
                    await bot.setup_task
                except asyncio.CancelledError:
                    pass

            # Don't run setup, so container remains None
            assert bot.container is None

            # Create cog without container (should use fallback)
            test_cog = TestCogForIntegration(bot)

            # Verify cog still initializes (with fallback services)
            assert test_cog.initialization_successful
            # Services should still be available (fallback implementations)
            assert test_cog.db_service is not None
            assert test_cog.bot_service is not None
            assert test_cog.config_service is not None

            # Cleanup
            if not bot.is_closed():
                await bot.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_memory_usage_with_dependency_injection(self, integration_bot):
        """Test that dependency injection doesn't significantly increase memory usage."""
        import psutil
        import os

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Setup bot with dependency injection
        await integration_bot.setup()

        # Create multiple cogs to test memory usage
        cogs = []
        for i in range(10):
            cog = TestCogForIntegration(integration_bot)
            await integration_bot.add_cog(cog, override=True)
            cogs.append(cog)

        # Get final memory usage
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        # Memory increase should be reasonable (less than 50MB for 10 cogs)
        max_allowed_increase = 50 * 1024 * 1024  # 50MB
        assert memory_increase < max_allowed_increase, (
            f"Memory usage increased too much: {memory_increase / 1024 / 1024:.2f}MB"
        )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_concurrent_service_resolution(self, integration_bot):
        """Test concurrent service resolution doesn't cause issues."""
        await integration_bot.setup()
        container = integration_bot.container

        async def resolve_services():
            """Resolve all services concurrently."""
            db_service = container.get(IDatabaseService)
            bot_service = container.get(IBotService)
            config_service = container.get(IConfigService)
            return db_service, bot_service, config_service

        # Run multiple concurrent resolutions
        tasks = [resolve_services() for _ in range(20)]
        results = await asyncio.gather(*tasks)

        # Verify all resolutions succeeded
        assert len(results) == 20
        for db_service, bot_service, config_service in results:
            assert db_service is not None
            assert bot_service is not None
            assert config_service is not None

        # Verify singleton behavior (all should be the same instances)
        first_result = results[0]
        for result in results[1:]:
            assert result[0] is first_result[0]  # Same DatabaseService
            assert result[1] is first_result[1]  # Same BotService
            assert result[2] is first_result[2]  # Same ConfigService

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_service_lifecycle_during_bot_shutdown(self, integration_bot):
        """Test service lifecycle during bot shutdown."""
        await integration_bot.setup()

        # Get references to services
        container = integration_bot.container
        db_service = container.get(IDatabaseService)
        bot_service = container.get(IBotService)
        config_service = container.get(IConfigService)

        # Verify services are available
        assert db_service is not None
        assert bot_service is not None
        assert config_service is not None

        # Shutdown the bot
        await integration_bot.shutdown()

        # Verify container is cleaned up
        assert integration_bot.container is None

        # Services should still be functional (they're not explicitly disposed)
        # This tests that shutdown doesn't break existing service references
        assert db_service.get_controller() is not None
        assert isinstance(bot_service.latency, float)
        assert isinstance(config_service.is_dev_mode(), bool)


class TestServiceRegistryIntegration:
    """Integration tests for service registry functionality."""

    @pytest.mark.integration
    def test_service_registry_configuration_with_real_bot(self):
        """Test service registry configuration with real bot instance."""
        # Create a mock bot
        bot = Mock(spec=commands.Bot)
        bot.latency = 0.1
        bot.user = Mock(spec=discord.ClientUser)
        bot.guilds = []

        # Configure container using service registry
        container = ServiceRegistry.configure_container(bot)

        # Verify container is properly configured
        assert isinstance(container, ServiceContainer)
        assert container.is_registered(IDatabaseService)
        assert container.is_registered(IBotService)
        assert container.is_registered(IConfigService)

        # Verify services can be resolved
        db_service = container.get(IDatabaseService)
        bot_service = container.get(IBotService)
        config_service = container.get(IConfigService)

        assert isinstance(db_service, DatabaseService)
        assert isinstance(bot_service, BotService)
        assert isinstance(config_service, ConfigService)

    @pytest.mark.integration
    def test_service_registry_validation(self):
        """Test service registry validation functionality."""
        # Create a properly configured container
        bot = Mock(spec=commands.Bot)
        container = ServiceRegistry.configure_container(bot)

        # Validation should pass
        assert ServiceRegistry.validate_container(container) is True

        # Create an incomplete container
        incomplete_container = ServiceContainer()
        incomplete_container.register_singleton(IDatabaseService, DatabaseService)
        # Missing other services

        # Validation should fail
        assert ServiceRegistry.validate_container(incomplete_container) is False

    @pytest.mark.integration
    def test_performance_measurement_utilities(self):
        """Test the performance measurement utilities work correctly."""
        # Create a test container
        bot = Mock(spec=commands.Bot)
        container = ServiceRegistry.configure_container(bot)

        # Measure service resolution performance
        metrics = measure_service_resolution_performance(
            container,
            IDatabaseService,
            iterations=50,
        )

        # Verify metrics structure
        assert "total_time" in metrics
        assert "average_time" in metrics
        assert "min_time" in metrics
        assert "max_time" in metrics
        assert "iterations" in metrics
        assert metrics["iterations"] == 50

        # Verify performance is reasonable
        assert metrics["average_time"] < 0.01  # Less than 10ms average
        assert metrics["total_time"] > 0  # Some time was taken
        assert metrics["min_time"] <= metrics["average_time"] <= metrics["max_time"]
