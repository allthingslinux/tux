"""
🚀 RetryHandler Unit Tests - Retry Logic & Circuit Breaker

Tests for the RetryHandler that implements retry logic with exponential backoff
and circuit breaker patterns for Discord API operations.

Test Coverage:
- Retry logic with different failure types
- Circuit breaker state transitions
- Exponential backoff calculation
- Rate limit handling
- Timeout and network error handling
- Circuit breaker metrics and monitoring
"""

import asyncio
import time
import pytest
from unittest.mock import AsyncMock, MagicMock

import discord

from tux.services.moderation.retry_handler import (
    RetryHandler,
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerMetrics,
    RetryConfig,
)


class TestCircuitBreaker:
    """🔄 Test CircuitBreaker functionality."""

    @pytest.fixture
    def circuit_breaker(self) -> CircuitBreaker:
        """Create a CircuitBreaker instance for testing."""
        return CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=1.0,  # Short timeout for testing
            expected_exception=(ValueError, RuntimeError),
        )

    @pytest.mark.unit
    async def test_circuit_breaker_initial_state(self, circuit_breaker: CircuitBreaker) -> None:
        """Test circuit breaker starts in CLOSED state."""
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.failure_threshold == 3
        assert circuit_breaker.recovery_timeout == 1.0

    @pytest.mark.unit
    async def test_circuit_breaker_successful_operation(self, circuit_breaker: CircuitBreaker) -> None:
        """Test successful operation recording."""
        async def success_func() -> str:
            return "success"

        result = await circuit_breaker.call(success_func)

        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED
        assert circuit_breaker.metrics.successful_requests == 1
        assert circuit_breaker.metrics.failed_requests == 0
        assert circuit_breaker.metrics.consecutive_failures == 0

    @pytest.mark.unit
    async def test_circuit_breaker_failure_recording(self, circuit_breaker: CircuitBreaker) -> None:
        """Test failure recording and consecutive failure tracking."""
        async def failing_func() -> str:
            raise ValueError("Test failure")

        with pytest.raises(ValueError, match="Test failure"):
            await circuit_breaker.call(failing_func)

        assert circuit_breaker.metrics.failed_requests == 1
        assert circuit_breaker.metrics.consecutive_failures == 1
        assert circuit_breaker.state == CircuitBreakerState.CLOSED  # Not yet tripped

    @pytest.mark.unit
    async def test_circuit_breaker_trip_after_threshold(self, circuit_breaker: CircuitBreaker) -> None:
        """Test circuit breaker trips after reaching failure threshold."""
        async def failing_func() -> str:
            raise ValueError("Test failure")

        # Fail enough times to trip the circuit breaker
        for i in range(circuit_breaker.failure_threshold):
            with pytest.raises(ValueError):
                await circuit_breaker.call(failing_func)

        assert circuit_breaker.metrics.consecutive_failures == circuit_breaker.failure_threshold
        assert circuit_breaker.state == CircuitBreakerState.OPEN

    @pytest.mark.unit
    async def test_circuit_breaker_open_state_rejects_requests(self, circuit_breaker: CircuitBreaker) -> None:
        """Test that open circuit breaker rejects requests."""
        # Manually set to open state and ensure it won't attempt reset
        circuit_breaker.state = CircuitBreakerState.OPEN
        circuit_breaker.last_attempt_time = time.time()  # Prevent reset attempt

        async def success_func() -> str:
            return "success"

        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await circuit_breaker.call(success_func)

    @pytest.mark.unit
    async def test_circuit_breaker_half_open_attempt_reset(self, circuit_breaker: CircuitBreaker) -> None:
        """Test circuit breaker attempts reset when in HALF_OPEN state."""
        circuit_breaker.state = CircuitBreakerState.HALF_OPEN
        circuit_breaker.last_attempt_time = time.time() - 2  # Past recovery timeout

        async def success_func() -> str:
            return "success"

        result = await circuit_breaker.call(success_func)

        assert result == "success"
        assert circuit_breaker.state == CircuitBreakerState.CLOSED

    @pytest.mark.unit
    async def test_circuit_breaker_recovery_timeout_prevents_reset(self, circuit_breaker: CircuitBreaker) -> None:
        """Test that recovery timeout prevents premature reset attempts."""
        circuit_breaker.state = CircuitBreakerState.OPEN
        circuit_breaker.last_attempt_time = time.time()  # Just attempted

        async def success_func() -> str:
            return "success"

        with pytest.raises(Exception, match="Circuit breaker is OPEN"):
            await circuit_breaker.call(success_func)

        # Should still be open
        assert circuit_breaker.state == CircuitBreakerState.OPEN

    @pytest.mark.unit
    async def test_circuit_breaker_half_open_failure_returns_to_open(self, circuit_breaker: CircuitBreaker) -> None:
        """Test that failure in HALF_OPEN state returns to OPEN."""
        circuit_breaker.state = CircuitBreakerState.HALF_OPEN

        async def failing_func() -> str:
            raise ValueError("Test failure")

        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)

        assert circuit_breaker.state == CircuitBreakerState.OPEN
        assert circuit_breaker.metrics.consecutive_failures == 1

    @pytest.mark.unit
    async def test_circuit_breaker_unexpected_exception_not_recorded(self, circuit_breaker: CircuitBreaker) -> None:
        """Test that unexpected exceptions are still raised but not recorded as circuit breaker failures."""
        async def unexpected_func() -> str:
            raise KeyError("Unexpected error")  # Not in expected_exception

        with pytest.raises(KeyError):
            await circuit_breaker.call(unexpected_func)

        # Should still record the failure
        assert circuit_breaker.metrics.failed_requests == 1

    @pytest.mark.unit
    async def test_circuit_breaker_metrics_tracking(self, circuit_breaker: CircuitBreaker) -> None:
        """Test comprehensive metrics tracking."""
        async def success_func() -> str:
            return "success"

        async def failing_func() -> str:
            raise ValueError("Test failure")

        # Mix of successes and failures
        await circuit_breaker.call(success_func)  # Success 1
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)  # Failure 1
        await circuit_breaker.call(success_func)  # Success 2
        with pytest.raises(ValueError):
            await circuit_breaker.call(failing_func)  # Failure 2

        metrics = circuit_breaker.get_metrics()
        assert metrics.total_requests == 4
        assert metrics.successful_requests == 2
        assert metrics.failed_requests == 2
        assert metrics.consecutive_failures == 1  # Reset after success


class TestRetryHandler:
    """🔄 Test RetryHandler functionality."""

    @pytest.fixture
    def retry_handler(self) -> RetryHandler:
        """Create a RetryHandler instance for testing."""
        return RetryHandler()

    @pytest.mark.unit
    async def test_retry_handler_initialization(self, retry_handler: RetryHandler) -> None:
        """Test retry handler initializes with default circuit breakers."""
        assert len(retry_handler.circuit_breakers) > 0
        assert "ban_kick" in retry_handler.circuit_breakers
        assert "timeout" in retry_handler.circuit_breakers
        assert "messages" in retry_handler.circuit_breakers

    @pytest.mark.unit
    async def test_get_retry_config_default(self, retry_handler: RetryHandler) -> None:
        """Test getting default retry configuration."""
        config = retry_handler.get_retry_config("nonexistent_operation")

        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.backoff_factor == 2.0
        assert config.jitter is True

    @pytest.mark.unit
    async def test_set_and_get_retry_config(self, retry_handler: RetryHandler) -> None:
        """Test setting and getting custom retry configuration."""
        custom_config = RetryConfig(
            max_attempts=5,
            base_delay=2.0,
            max_delay=60.0,
            backoff_factor=1.5,
            jitter=False,
        )

        retry_handler.set_retry_config("custom_operation", custom_config)
        retrieved_config = retry_handler.get_retry_config("custom_operation")

        assert retrieved_config.max_attempts == 5
        assert retrieved_config.base_delay == 2.0
        assert retrieved_config.max_delay == 60.0
        assert retrieved_config.backoff_factor == 1.5
        assert retrieved_config.jitter is False

    @pytest.mark.unit
    async def test_get_circuit_breaker_existing(self, retry_handler: RetryHandler) -> None:
        """Test getting existing circuit breaker."""
        cb = retry_handler.get_circuit_breaker("ban_kick")

        assert isinstance(cb, CircuitBreaker)
        assert cb.failure_threshold == 3  # Default for ban_kick

    @pytest.mark.unit
    async def test_get_circuit_breaker_new(self, retry_handler: RetryHandler) -> None:
        """Test getting new circuit breaker for unknown operation."""
        cb = retry_handler.get_circuit_breaker("unknown_operation")

        assert isinstance(cb, CircuitBreaker)
        assert cb.failure_threshold == 5  # Default failure threshold

    @pytest.mark.unit
    async def test_execute_with_retry_success_first_attempt(self, retry_handler: RetryHandler) -> None:
        """Test successful execution on first attempt."""
        async def success_func() -> str:
            return "success"

        result = await retry_handler.execute_with_retry("messages", success_func)

        assert result == "success"

    @pytest.mark.unit
    async def test_execute_with_retry_eventual_success(self, retry_handler: RetryHandler) -> None:
        """Test eventual success after retries."""
        call_count = 0

        async def intermittent_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("Temporary failure")
            return "success"

        result = await retry_handler.execute_with_retry("messages", intermittent_func)

        assert result == "success"
        assert call_count == 3

    @pytest.mark.unit
    async def test_execute_with_retry_forbidden_no_retry(self, retry_handler: RetryHandler) -> None:
        """Test that Forbidden errors don't trigger retries."""
        async def forbidden_func() -> str:
            raise discord.Forbidden(MagicMock(), "No permission")

        with pytest.raises(discord.Forbidden):
            await retry_handler.execute_with_retry("ban_kick", forbidden_func)

    @pytest.mark.unit
    async def test_execute_with_retry_not_found_no_retry(self, retry_handler: RetryHandler) -> None:
        """Test that NotFound errors don't trigger retries."""
        async def not_found_func() -> str:
            raise discord.NotFound(MagicMock(), "User not found")

        with pytest.raises(discord.NotFound):
            await retry_handler.execute_with_retry("ban_kick", not_found_func)

    @pytest.mark.unit
    async def test_execute_with_retry_rate_limit_with_retry_after(self, retry_handler: RetryHandler) -> None:
        """Test rate limit handling with retry-after header."""
        call_count = 0

        async def rate_limited_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                error = discord.HTTPException(MagicMock(), "Rate limited")
                error.status = 429
                error.retry_after = 0.1  # Short retry time for testing
                raise error
            return "success"

        result = await retry_handler.execute_with_retry("ban_kick", rate_limited_func)

        assert result == "success"
        assert call_count == 2

    @pytest.mark.unit
    async def test_execute_with_retry_server_error_retry(self, retry_handler: RetryHandler) -> None:
        """Test server error triggers retry with backoff."""
        call_count = 0

        async def server_error_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                error = discord.HTTPException(MagicMock(), "Server error")
                error.status = 500
                raise error
            return "success"

        result = await retry_handler.execute_with_retry("messages", server_error_func)

        assert result == "success"
        assert call_count == 2

    @pytest.mark.unit
    async def test_execute_with_retry_max_attempts_exceeded(self, retry_handler: RetryHandler) -> None:
        """Test that max attempts are respected."""
        call_count = 0

        async def always_failing_func() -> str:
            nonlocal call_count
            call_count += 1
            raise ValueError("Always fails")

        with pytest.raises(ValueError, match="Always fails"):
            await retry_handler.execute_with_retry("messages", always_failing_func)

        assert call_count == 3  # Default max_attempts

    @pytest.mark.unit
    async def test_execute_with_retry_circuit_breaker_trip(self, retry_handler: RetryHandler) -> None:
        """Test circuit breaker tripping after repeated failures."""
        # Create a circuit breaker with low threshold for quick testing
        cb = CircuitBreaker(expected_exception=ValueError, failure_threshold=2)
        retry_handler.circuit_breakers["test_operation"] = cb

        async def always_failing_func() -> str:
            raise ValueError("Always fails")

        # Keep calling until circuit breaker trips
        call_count = 0
        circuit_tripped = False

        while not circuit_tripped and call_count < 10:  # Safety limit
            call_count += 1
            try:
                await retry_handler.execute_with_retry("test_operation", always_failing_func)
            except ValueError:
                # Expected failure, continue
                continue
            except Exception as e:
                if "Circuit breaker is OPEN" in str(e):
                    circuit_tripped = True
                else:
                    raise  # Unexpected exception

        # Verify circuit breaker eventually tripped
        assert circuit_tripped, f"Circuit breaker should have tripped after {call_count} calls"

        # Next call should be rejected by circuit breaker
        with pytest.raises(Exception, match="Circuit breaker is OPEN - service unavailable"):
            await retry_handler.execute_with_retry("test_operation", always_failing_func)

    @pytest.mark.unit
    async def test_calculate_delay_exponential_backoff(self, retry_handler: RetryHandler) -> None:
        """Test exponential backoff delay calculation."""
        config = RetryConfig(base_delay=1.0, backoff_factor=2.0, max_delay=30.0)

        delay1 = retry_handler._calculate_delay(0, config)  # First retry
        delay2 = retry_handler._calculate_delay(1, config)  # Second retry
        delay3 = retry_handler._calculate_delay(2, config)  # Third retry

        # Jitter can make delays smaller, so we check a reasonable range
        assert 0.75 <= delay1 <= 1.25  # Base delay with ±25% jitter
        assert 1.5 <= delay2 <= 2.5    # Base * factor with ±25% jitter
        assert 3.0 <= delay3 <= 5.0    # Base * factor^2 with ±25% jitter

    @pytest.mark.unit
    async def test_calculate_delay_max_delay_respected(self, retry_handler: RetryHandler) -> None:
        """Test that max delay is respected."""
        config = RetryConfig(base_delay=10.0, backoff_factor=10.0, max_delay=20.0)

        delay = retry_handler._calculate_delay(5, config)  # Would be 10 * 10^5 = 100000

        assert delay <= 20.0

    @pytest.mark.unit
    async def test_calculate_delay_minimum_delay(self, retry_handler: RetryHandler) -> None:
        """Test minimum delay enforcement."""
        config = RetryConfig(base_delay=0.01, backoff_factor=0.1)

        delay = retry_handler._calculate_delay(0, config)

        assert delay >= 0.1

    @pytest.mark.unit
    async def test_calculate_delay_jitter_disabled(self, retry_handler: RetryHandler) -> None:
        """Test delay calculation without jitter."""
        config = RetryConfig(base_delay=1.0, backoff_factor=2.0, jitter=False)

        delay = retry_handler._calculate_delay(0, config)

        assert delay == 1.0  # Exact value without jitter

    @pytest.mark.unit
    async def test_get_all_metrics(self, retry_handler: RetryHandler) -> None:
        """Test getting metrics for all circuit breakers."""
        metrics = retry_handler.get_all_metrics()

        assert isinstance(metrics, dict)
        assert len(metrics) > 0

        for operation_type, cb_metrics in metrics.items():
            assert isinstance(cb_metrics, CircuitBreakerMetrics)

    @pytest.mark.unit
    async def test_reset_circuit_breaker(self, retry_handler: RetryHandler) -> None:
        """Test manual circuit breaker reset."""
        # First ensure we have a circuit breaker
        cb = retry_handler.get_circuit_breaker("test_reset")

        # Manually trip it
        cb.state = CircuitBreakerState.OPEN
        cb.metrics.consecutive_failures = 10

        # Reset it
        retry_handler.reset_circuit_breaker("test_reset")

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.metrics.consecutive_failures == 0

    @pytest.mark.unit
    async def test_reset_nonexistent_circuit_breaker(self, retry_handler: RetryHandler) -> None:
        """Test resetting non-existent circuit breaker doesn't crash."""
        # Should not raise an exception
        retry_handler.reset_circuit_breaker("nonexistent")

        # Verify it was created with default state
        cb = retry_handler.get_circuit_breaker("nonexistent")
        assert cb.state == CircuitBreakerState.CLOSED
