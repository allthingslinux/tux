"""
Retry logic and circuit breaker patterns for Discord API operations.

Handles temporary failures, rate limiting, and cascading errors with
exponential backoff and circuit breaker patterns.
"""

import asyncio
import random
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from enum import Enum
from typing import Any

import discord
from loguru import logger


class CircuitBreakerState(Enum):
    """States for the circuit breaker pattern."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    consecutive_failures: int = 0
    last_failure_time: float = 0.0
    last_success_time: float = 0.0


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    jitter: bool = True


class CircuitBreaker:
    """
    Circuit breaker implementation for Discord API calls.

    Prevents cascading failures by temporarily stopping requests to failing services.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: tuple[type[Exception], ...] = (Exception,),
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.state = CircuitBreakerState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self.last_attempt_time = 0.0

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit breaker."""
        if self.state != CircuitBreakerState.OPEN:
            return False
        return time.time() - self.last_attempt_time >= self.recovery_timeout

    def _record_success(self) -> None:
        """Record a successful request."""
        self.metrics.successful_requests += 1
        self.metrics.consecutive_failures = 0
        self.metrics.last_success_time = time.time()

        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info("Circuit breaker resetting to CLOSED state")
            self.state = CircuitBreakerState.CLOSED

    def _record_failure(self) -> None:
        """Record a failed request."""
        self.metrics.failed_requests += 1
        self.metrics.consecutive_failures += 1
        self.metrics.last_failure_time = time.time()

        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.warning("Circuit breaker returning to OPEN state")
            self.state = CircuitBreakerState.OPEN
        elif self.state == CircuitBreakerState.CLOSED and self.metrics.consecutive_failures >= self.failure_threshold:
            logger.warning(f"Circuit breaker opening after {self.metrics.consecutive_failures} failures")
            self.state = CircuitBreakerState.OPEN
            self.last_attempt_time = time.time()

    async def call(self, func: Callable[..., Coroutine[Any, Any, Any]], *args: Any, **kwargs: Any) -> Any:
        """
        Execute a function with circuit breaker protection.

        Parameters
        ----------
        func : Callable
            The async function to execute
        *args : Any
            Positional arguments for the function
        **kwargs : Any
            Keyword arguments for the function

        Returns
        -------
        Any
            The result of the function call

        Raises
        ------
        Exception
            If circuit is open or function fails
        """
        self.metrics.total_requests += 1

        # Check if we should attempt to reset
        if self.state == CircuitBreakerState.OPEN and self._should_attempt_reset():
            logger.info("Circuit breaker attempting reset to HALF_OPEN")
            self.state = CircuitBreakerState.HALF_OPEN

        # Reject request if circuit is open
        if self.state == CircuitBreakerState.OPEN:
            msg = "Circuit breaker is OPEN - service unavailable"
            raise RuntimeError(msg)

        try:
            result = await func(*args, **kwargs)
            self._record_success()
        except Exception as e:
            # Record failure for any exception, but only re-raise expected exceptions
            self._record_failure()
            if isinstance(e, self.expected_exception):
                raise
            # For unexpected exceptions, we still record the failure but don't re-raise
            # Instead, we'll re-raise the original exception
            raise
        else:
            return result

    def get_metrics(self) -> CircuitBreakerMetrics:
        """Get current circuit breaker metrics."""
        return self.metrics

    def get_state(self) -> CircuitBreakerState:
        """Get current circuit breaker state."""
        return self.state


class RetryHandler:
    """
    Handles retry logic with exponential backoff for Discord operations.

    Provides intelligent retry behavior for different types of failures.
    """

    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.retry_configs: dict[str, RetryConfig] = {}

        # Default circuit breakers for common Discord operations
        self._setup_default_circuit_breakers()

    def _setup_default_circuit_breakers(self) -> None:
        """Set up default circuit breakers for common operations."""
        # Ban/Kick operations
        self.circuit_breakers["ban_kick"] = CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30.0,
            expected_exception=(discord.Forbidden, discord.HTTPException, discord.NotFound),
        )

        # Timeout operations
        self.circuit_breakers["timeout"] = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60.0,
            expected_exception=(discord.Forbidden, discord.HTTPException),
        )

        # Message operations
        self.circuit_breakers["messages"] = CircuitBreaker(
            failure_threshold=10,
            recovery_timeout=120.0,
            expected_exception=(discord.HTTPException,),
        )

    def get_retry_config(self, operation_type: str) -> RetryConfig:
        """Get retry configuration for an operation type."""
        if operation_type in self.retry_configs:
            return self.retry_configs[operation_type]

        # Default retry config
        return RetryConfig(max_attempts=3, base_delay=1.0, max_delay=30.0, backoff_factor=2.0, jitter=True)

    def set_retry_config(self, operation_type: str, config: RetryConfig) -> None:
        """Set retry configuration for an operation type."""
        self.retry_configs[operation_type] = config

    def get_circuit_breaker(self, operation_type: str) -> CircuitBreaker:
        """Get circuit breaker for an operation type."""
        if operation_type not in self.circuit_breakers:
            # Create a default circuit breaker
            self.circuit_breakers[operation_type] = CircuitBreaker(
                expected_exception=(discord.HTTPException, discord.Forbidden, discord.NotFound),
            )
        return self.circuit_breakers[operation_type]

    async def execute_with_retry(  # noqa: PLR0912, PLR0915
        self,
        operation_type: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:  # sourcery skip: low-code-quality, use-named-expression
        """
        Execute a function with retry logic and circuit breaker protection.

        Parameters
        ----------
        operation_type : str
            Type of operation (e.g., 'ban_kick', 'timeout', 'messages')
        func : Callable
            The async function to execute
        *args : Any
            Positional arguments for the function
        **kwargs : Any
            Keyword arguments for the function

        Returns
        -------
        Any
            The result of the function call

        Raises
        ------
        Exception
            If all retry attempts fail or circuit breaker is open
        """
        config = self.get_retry_config(operation_type)
        circuit_breaker = self.get_circuit_breaker(operation_type)

        last_exception = None
        result = None

        for attempt in range(config.max_attempts):
            try:
                logger.info(f"Attempting {operation_type} (attempt {attempt + 1}/{config.max_attempts})")

                # Use circuit breaker
                result = await circuit_breaker.call(func, *args, **kwargs)

                if attempt > 0:
                    logger.info(f"{operation_type} succeeded on attempt {attempt + 1}")

                # Success! Break out of retry loop
                break
            except discord.Forbidden as e:
                # Don't retry permission errors
                logger.error(f"Permission denied for {operation_type}: {e}")
                raise
            except discord.NotFound as e:
                # Don't retry not found errors
                logger.error(f"Resource not found for {operation_type}: {e}")
                raise
            except discord.HTTPException as e:
                last_exception = e
                if e.status == 429:
                    # Rate limited - use retry-after header if available
                    retry_after = getattr(e, "retry_after", None)
                    if retry_after:
                        delay = min(retry_after, config.max_delay)
                        logger.warning(f"Rate limited, waiting {delay}s before retry")
                        await asyncio.sleep(delay)
                        continue

                elif e.status >= 500:
                    # Server error - retry with backoff
                    if attempt < config.max_attempts - 1:
                        delay = self._calculate_delay(attempt, config)
                        logger.warning(f"Server error ({e.status}), retrying in {delay}s")
                        await asyncio.sleep(delay)
                        continue

                # Client error or final attempt
                logger.error(f"HTTP error for {operation_type}: {e}")
                raise

            except Exception as e:
                last_exception = e
                # Don't retry circuit breaker errors - they're meant to be fast failures
                if "Circuit breaker is OPEN" in str(e):
                    logger.warning(f"Circuit breaker is open for {operation_type}, not retrying: {e}")
                    raise
                if attempt < config.max_attempts - 1:
                    delay = self._calculate_delay(attempt, config)
                    logger.warning(f"Unexpected error, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                    continue
                logger.error(f"All retry attempts failed for {operation_type}: {e}")
                raise
        return result

        # This should never be reached, but just in case
        if last_exception:
            raise last_exception
        msg = f"All retry attempts failed for {operation_type}"
        raise RuntimeError(msg)

    def _calculate_delay(self, attempt: int, config: RetryConfig) -> float:
        """Calculate delay for exponential backoff with optional jitter."""
        delay = config.base_delay * (config.backoff_factor**attempt)
        delay = min(delay, config.max_delay)

        if config.jitter:
            # Add random jitter (±25%)
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0.1, delay)  # Minimum 100ms delay

    def get_all_metrics(self) -> dict[str, CircuitBreakerMetrics]:
        """Get metrics for all circuit breakers."""
        return {operation_type: cb.get_metrics() for operation_type, cb in self.circuit_breakers.items()}

    def reset_circuit_breaker(self, operation_type: str) -> None:
        """Manually reset a circuit breaker to closed state."""
        if operation_type in self.circuit_breakers:
            logger.info(f"Manually resetting circuit breaker for {operation_type}")
            self.circuit_breakers[operation_type].state = CircuitBreakerState.CLOSED
            self.circuit_breakers[operation_type].metrics.consecutive_failures = 0


# Global instance for the moderation system
retry_handler = RetryHandler()
