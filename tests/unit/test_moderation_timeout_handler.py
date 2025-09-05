"""
🚀 TimeoutHandler Unit Tests - Timeout Management & Graceful Degradation

Tests for the TimeoutHandler that manages timeouts and implements graceful
degradation strategies for moderation operations.

Test Coverage:
- Timeout configuration management
- Graceful degradation with extended timeouts
- DM-specific timeout handling
- Database operation timeouts
- Discord API timeouts
- Timeout error handling and recovery
"""

import asyncio
import pytest
from unittest.mock import AsyncMock

from tux.services.moderation.timeout_handler import (
    TimeoutHandler,
    TimeoutConfig,
)


class TestTimeoutConfig:
    """⚙️ Test TimeoutConfig functionality."""

    @pytest.mark.unit
    def test_timeout_config_creation(self) -> None:
        """Test TimeoutConfig creation with all parameters."""
        config = TimeoutConfig(
            operation_timeout=15.0,
            dm_timeout=3.0,
            database_timeout=10.0,
            api_timeout=8.0,
            max_extend_attempts=2,
            extend_factor=1.5,
            graceful_degradation=True,
        )

        assert config.operation_timeout == 15.0
        assert config.dm_timeout == 3.0
        assert config.database_timeout == 10.0
        assert config.api_timeout == 8.0
        assert config.max_extend_attempts == 2
        assert config.extend_factor == 1.5
        assert config.graceful_degradation is True

    @pytest.mark.unit
    def test_timeout_config_defaults(self) -> None:
        """Test TimeoutConfig with default values."""
        config = TimeoutConfig(operation_timeout=20.0)

        assert config.operation_timeout == 20.0
        assert config.dm_timeout == 3.0  # Default
        assert config.database_timeout == 10.0  # Default
        assert config.api_timeout == 5.0  # Default
        assert config.max_extend_attempts == 2  # Default
        assert config.extend_factor == 1.5  # Default
        assert config.graceful_degradation is True  # Default


class TestTimeoutHandler:
    """⏰ Test TimeoutHandler functionality."""

    @pytest.fixture
    def timeout_handler(self) -> TimeoutHandler:
        """Create a TimeoutHandler instance for testing."""
        return TimeoutHandler()

    @pytest.mark.unit
    async def test_timeout_handler_initialization(self, timeout_handler: TimeoutHandler) -> None:
        """Test timeout handler initializes with default configurations."""
        assert len(timeout_handler._configs) > 0
        assert "ban_kick" in timeout_handler._configs
        assert "timeout" in timeout_handler._configs
        assert "messages" in timeout_handler._configs
        assert "default" in timeout_handler._configs

    @pytest.mark.unit
    async def test_get_config_existing_operation(self, timeout_handler: TimeoutHandler) -> None:
        """Test getting configuration for existing operation type."""
        config = timeout_handler.get_config("ban_kick")

        assert isinstance(config, TimeoutConfig)
        assert config.operation_timeout == 15.0  # ban_kick specific
        assert config.dm_timeout == 2.0  # ban_kick specific

    @pytest.mark.unit
    async def test_get_config_default_fallback(self, timeout_handler: TimeoutHandler) -> None:
        """Test getting configuration falls back to default for unknown operation."""
        config = timeout_handler.get_config("unknown_operation")

        assert isinstance(config, TimeoutConfig)
        assert config.operation_timeout == 25.0  # default value

    @pytest.mark.unit
    async def test_execute_with_timeout_success(self, timeout_handler: TimeoutHandler) -> None:
        """Test successful execution within timeout."""
        async def quick_func() -> str:
            await asyncio.sleep(0.1)
            return "success"

        result = await timeout_handler.execute_with_timeout("messages", quick_func)

        assert result == "success"

    @pytest.mark.unit
    async def test_execute_with_timeout_timeout_error(self, timeout_handler: TimeoutHandler) -> None:
        """Test timeout error when operation takes too long."""
        # Set a very short timeout for this test
        timeout_handler._configs["messages"] = TimeoutConfig(
            operation_timeout=0.1,  # Very short timeout
            dm_timeout=5.0,
            database_timeout=10.0,
            api_timeout=15.0,
            max_extend_attempts=0,  # No graceful degradation
            graceful_degradation=False,
        )

        async def slow_func() -> str:
            await asyncio.sleep(1)  # Longer than timeout
            return "success"

        with pytest.raises(asyncio.TimeoutError):
            await timeout_handler.execute_with_timeout("messages", slow_func)

    @pytest.mark.unit
    async def test_execute_with_timeout_graceful_degradation_disabled(self, timeout_handler: TimeoutHandler) -> None:
        """Test timeout without graceful degradation."""
        # Create custom config with graceful degradation disabled
        timeout_handler._configs["test"] = TimeoutConfig(
            operation_timeout=0.5,
            graceful_degradation=False,
        )

        async def slow_func() -> str:
            await asyncio.sleep(1)  # Longer than timeout
            return "success"

        with pytest.raises(asyncio.TimeoutError):
            await timeout_handler.execute_with_timeout("test", slow_func)

    @pytest.mark.unit
    async def test_execute_with_timeout_graceful_degradation_success(self, timeout_handler: TimeoutHandler) -> None:
        """Test successful graceful degradation after initial timeout."""
        # Create custom config with short initial timeout but successful retry
        timeout_handler._configs["test"] = TimeoutConfig(
            operation_timeout=0.1,  # Very short
            max_extend_attempts=2,
            extend_factor=2.0,
        )

        call_count = 0
        async def eventually_quick_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                await asyncio.sleep(0.2)  # First call times out
            else:
                await asyncio.sleep(0.05)  # Subsequent calls succeed
            return "success"

        result = await timeout_handler.execute_with_timeout("test", eventually_quick_func)

        assert result == "success"
        assert call_count == 2  # One timeout, one success

    @pytest.mark.unit
    async def test_execute_with_timeout_max_extend_attempts_reached(self, timeout_handler: TimeoutHandler) -> None:
        """Test graceful degradation fails after max extend attempts."""
        timeout_handler._configs["test"] = TimeoutConfig(
            operation_timeout=0.1,
            max_extend_attempts=1,  # Only one retry
            extend_factor=2.0,
        )

        async def always_slow_func() -> str:
            await asyncio.sleep(1)  # Always too slow
            return "success"

        with pytest.raises(asyncio.TimeoutError):
            await timeout_handler.execute_with_timeout("test", always_slow_func)

    @pytest.mark.unit
    async def test_execute_with_timeout_operation_takes_too_long(self, timeout_handler: TimeoutHandler) -> None:
        """Test when operation takes longer than all extended timeouts combined."""
        timeout_handler._configs["test"] = TimeoutConfig(
            operation_timeout=0.1,
            max_extend_attempts=2,
            extend_factor=2.0,
        )

        async def very_slow_func() -> str:
            await asyncio.sleep(10)  # Much longer than extended timeouts
            return "success"

        with pytest.raises(asyncio.TimeoutError):
            await timeout_handler.execute_with_timeout("test", very_slow_func)

    @pytest.mark.unit
    async def test_execute_dm_with_timeout_success(self, timeout_handler: TimeoutHandler) -> None:
        """Test successful DM execution within timeout."""
        async def quick_dm_func() -> str:
            await asyncio.sleep(0.05)
            return "DM sent"

        result = await timeout_handler.execute_dm_with_timeout("messages", quick_dm_func)

        assert result == "DM sent"

    @pytest.mark.unit
    async def test_execute_dm_with_timeout_timeout_returns_none(self, timeout_handler: TimeoutHandler) -> None:
        """Test DM timeout returns None (graceful failure)."""
        async def slow_dm_func() -> str:
            await asyncio.sleep(6)  # Longer than DM timeout (5.0s)
            return "DM sent"

        result = await timeout_handler.execute_dm_with_timeout("messages", slow_dm_func)

        assert result is None

    @pytest.mark.unit
    async def test_execute_dm_with_timeout_exception_returns_none(self, timeout_handler: TimeoutHandler) -> None:
        """Test DM exception returns None (graceful failure)."""
        async def failing_dm_func() -> str:
            raise ValueError("DM failed")

        result = await timeout_handler.execute_dm_with_timeout("messages", failing_dm_func)

        assert result is None

    @pytest.mark.unit
    async def test_execute_database_with_timeout_success(self, timeout_handler: TimeoutHandler) -> None:
        """Test successful database execution within timeout."""
        async def quick_db_func() -> str:
            await asyncio.sleep(0.05)
            return "DB result"

        result = await timeout_handler.execute_database_with_timeout("messages", quick_db_func)

        assert result == "DB result"

    @pytest.mark.unit
    async def test_execute_database_with_timeout_timeout_error(self, timeout_handler: TimeoutHandler) -> None:
        """Test database timeout raises exception (not graceful)."""
        async def slow_db_func() -> str:
            await asyncio.sleep(20)  # Longer than database timeout
            return "DB result"

        with pytest.raises(asyncio.TimeoutError):
            await timeout_handler.execute_database_with_timeout("messages", slow_db_func)

    @pytest.mark.unit
    async def test_execute_database_with_timeout_exception_raised(self, timeout_handler: TimeoutHandler) -> None:
        """Test database exception is raised (not graceful)."""
        async def failing_db_func() -> str:
            raise ConnectionError("Database connection failed")

        with pytest.raises(ConnectionError):
            await timeout_handler.execute_database_with_timeout("messages", failing_db_func)

    @pytest.mark.unit
    async def test_execute_api_with_timeout_success(self, timeout_handler: TimeoutHandler) -> None:
        """Test successful Discord API execution within timeout."""
        async def quick_api_func() -> str:
            await asyncio.sleep(0.05)
            return "API result"

        result = await timeout_handler.execute_api_with_timeout("messages", quick_api_func)

        assert result == "API result"

    @pytest.mark.unit
    async def test_execute_api_with_timeout_timeout_error(self, timeout_handler: TimeoutHandler) -> None:
        """Test Discord API timeout raises exception."""
        async def slow_api_func() -> str:
            await asyncio.sleep(20)  # Longer than API timeout
            return "API result"

        with pytest.raises(asyncio.TimeoutError):
            await timeout_handler.execute_api_with_timeout("messages", slow_api_func)

    @pytest.mark.unit
    async def test_execute_api_with_timeout_exception_raised(self, timeout_handler: TimeoutHandler) -> None:
        """Test Discord API exception is raised."""
        async def failing_api_func() -> str:
            raise RuntimeError("API call failed")

        with pytest.raises(RuntimeError):
            await timeout_handler.execute_api_with_timeout("messages", failing_api_func)

    @pytest.mark.unit
    async def test_different_operation_types_have_different_configs(self, timeout_handler: TimeoutHandler) -> None:
        """Test that different operation types have appropriately different timeout configs."""
        ban_config = timeout_handler.get_config("ban_kick")
        timeout_config = timeout_handler.get_config("timeout")
        messages_config = timeout_handler.get_config("messages")

        # Ban operations should have shorter timeouts (more critical)
        assert ban_config.operation_timeout < messages_config.operation_timeout

        # Timeout operations should have moderate timeouts
        assert timeout_config.operation_timeout > ban_config.operation_timeout
        assert timeout_config.operation_timeout < messages_config.operation_timeout

        # Messages should have longest timeouts (least critical)
        assert messages_config.operation_timeout > ban_config.operation_timeout

    @pytest.mark.unit
    async def test_timeout_handler_handles_multiple_concurrent_operations(self, timeout_handler: TimeoutHandler) -> None:
        """Test timeout handler can handle multiple concurrent operations."""
        async def concurrent_func(task_id: int) -> str:
            await asyncio.sleep(0.1)
            return f"task_{task_id}"

        # Start multiple operations concurrently
        tasks = [
            timeout_handler.execute_with_timeout("messages", concurrent_func, i)
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)

        assert len(results) == 5
        assert set(results) == {"task_0", "task_1", "task_2", "task_3", "task_4"}

    @pytest.mark.unit
    async def test_timeout_handler_config_isolation(self, timeout_handler: TimeoutHandler) -> None:
        """Test that different operation configs don't interfere with each other."""
        # Get configs for different operations
        config1 = timeout_handler.get_config("ban_kick")
        config2 = timeout_handler.get_config("messages")

        # Modify one config (this should not affect the other)
        original_timeout = config1.operation_timeout
        config1.operation_timeout = 999  # This is just a reference, not stored

        # Get the config again - should be unchanged
        config1_again = timeout_handler.get_config("ban_kick")
        assert config1_again.operation_timeout == original_timeout

        # Other config should be unaffected
        config2_again = timeout_handler.get_config("messages")
        assert config2_again.operation_timeout != 999
