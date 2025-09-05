"""
Timeout handling for moderation operations with graceful degradation.

Provides configurable timeouts and fallback strategies for different operation types.
"""

import asyncio
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any, TypeVar

from loguru import logger

T = TypeVar("T")


@dataclass
class TimeoutConfig:
    """Configuration for timeout handling."""

    operation_timeout: float
    dm_timeout: float = 3.0
    database_timeout: float = 10.0
    api_timeout: float = 5.0
    max_extend_attempts: int = 2
    extend_factor: float = 1.5
    graceful_degradation: bool = True


class TimeoutHandler:
    """
    Handles timeouts for moderation operations with graceful degradation.

    Provides different timeout strategies based on operation type and
    implements fallback mechanisms for timeout scenarios.
    """

    def __init__(self):
        self._configs: dict[str, TimeoutConfig] = {}
        self._setup_default_configs()

    def _setup_default_configs(self) -> None:
        """Set up default timeout configurations for different operations."""
        # Ban/Kick operations - critical, shorter timeout
        self._configs["ban_kick"] = TimeoutConfig(
            operation_timeout=15.0,
            dm_timeout=2.0,
            database_timeout=5.0,
            api_timeout=8.0,
            max_extend_attempts=1,
            graceful_degradation=True,
        )

        # Timeout operations - medium priority
        self._configs["timeout"] = TimeoutConfig(
            operation_timeout=20.0,
            dm_timeout=3.0,
            database_timeout=7.0,
            api_timeout=10.0,
            max_extend_attempts=2,
            graceful_degradation=True,
        )

        # Message operations - lower priority, longer timeout
        self._configs["messages"] = TimeoutConfig(
            operation_timeout=30.0,
            dm_timeout=5.0,
            database_timeout=10.0,
            api_timeout=15.0,
            max_extend_attempts=3,
            graceful_degradation=True,
        )

        # Default config
        self._configs["default"] = TimeoutConfig(
            operation_timeout=25.0,
            dm_timeout=3.0,
            database_timeout=8.0,
            api_timeout=12.0,
            max_extend_attempts=2,
            graceful_degradation=True,
        )

    def get_config(self, operation_type: str) -> TimeoutConfig:
        """Get timeout configuration for an operation type."""
        config = self._configs.get(operation_type, self._configs["default"])
        # Return a copy to prevent modification of the stored config
        return TimeoutConfig(
            operation_timeout=config.operation_timeout,
            dm_timeout=config.dm_timeout,
            database_timeout=config.database_timeout,
            api_timeout=config.api_timeout,
            max_extend_attempts=config.max_extend_attempts,
            extend_factor=config.extend_factor,
            graceful_degradation=config.graceful_degradation,
        )

    async def execute_with_timeout(
        self,
        operation_type: str,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Execute a function with timeout handling and graceful degradation.

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
        T
            The result of the function call

        Raises
        ------
        asyncio.TimeoutError
            If operation times out and cannot be gracefully degraded
        Exception
            If the operation fails
        """
        config = self.get_config(operation_type)
        start_time = time.time()

        try:
            # Initial attempt with base timeout
            logger.debug(f"Executing {operation_type} with timeout {config.operation_timeout}s")
            return await asyncio.wait_for(func(*args, **kwargs), timeout=config.operation_timeout)

        except TimeoutError:
            if not config.graceful_degradation:
                logger.error(f"{operation_type} timed out without graceful degradation")
                raise

            # Attempt graceful degradation with extended timeouts
            for attempt in range(config.max_extend_attempts):
                extended_timeout = config.operation_timeout * (config.extend_factor ** (attempt + 1))

                logger.warning(
                    f"{operation_type} timed out, attempting graceful degradation "
                    f"(attempt {attempt + 1}/{config.max_extend_attempts}, "
                    f"extended timeout: {extended_timeout}s)",
                )

                try:
                    # Check if we should still attempt (not too much time has passed)
                    elapsed = time.time() - start_time
                    if elapsed > extended_timeout * 2:
                        logger.error(f"{operation_type} has taken too long ({elapsed:.1f}s), giving up")
                        msg = f"Operation took too long: {elapsed:.1f}s"
                        raise TimeoutError(msg)  # noqa: TRY301

                    return await asyncio.wait_for(func(*args, **kwargs), timeout=extended_timeout)

                except TimeoutError:
                    if attempt == config.max_extend_attempts - 1:
                        logger.error(
                            f"{operation_type} failed all {config.max_extend_attempts} graceful degradation attempts",
                        )
                        raise
                    continue

            # This should not be reached
            msg = f"{operation_type} timed out after all attempts"
            raise TimeoutError(msg) from None

    async def execute_dm_with_timeout(
        self,
        operation_type: str,
        dm_func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T | None:
        """
        Execute a DM function with specific DM timeout handling.

        DM operations are allowed to fail gracefully without affecting the main operation.

        Parameters
        ----------
        operation_type : str
            Type of operation for timeout configuration
        dm_func : Callable
            The DM function to execute
        *args : Any
            Positional arguments for the DM function
        **kwargs : Any
            Keyword arguments for the DM function

        Returns
        -------
        T | None
            The result of the DM function, or None if it timed out
        """
        config = self.get_config(operation_type)

        try:
            logger.debug(f"Sending DM with timeout {config.dm_timeout}s")
            return await asyncio.wait_for(dm_func(*args, **kwargs), timeout=config.dm_timeout)
        except TimeoutError:
            logger.warning(f"DM timed out after {config.dm_timeout}s")
            return None
        except Exception as e:
            logger.warning(f"DM failed: {e}")
            return None

    async def execute_database_with_timeout(
        self,
        operation_type: str,
        db_func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Execute a database function with specific database timeout handling.

        Database operations are critical and should not fail gracefully.

        Parameters
        ----------
        operation_type : str
            Type of operation for timeout configuration
        db_func : Callable
            The database function to execute
        *args : Any
            Positional arguments for the database function
        **kwargs : Any
            Keyword arguments for the database function

        Returns
        -------
        T
            The result of the database function

        Raises
        ------
        asyncio.TimeoutError
            If database operation times out
        Exception
            If database operation fails
        """
        config = self.get_config(operation_type)

        try:
            logger.debug(f"Executing database operation with timeout {config.database_timeout}s")
            return await asyncio.wait_for(db_func(*args, **kwargs), timeout=config.database_timeout)
        except TimeoutError:
            logger.critical(f"Database operation timed out after {config.database_timeout}s")
            raise
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
            raise

    async def execute_api_with_timeout(
        self,
        operation_type: str,
        api_func: Callable[..., Coroutine[Any, Any, T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Execute a Discord API function with specific API timeout handling.

        Parameters
        ----------
        operation_type : str
            Type of operation for timeout configuration
        api_func : Callable
            The Discord API function to execute
        *args : Any
            Positional arguments for the API function
        **kwargs : Any
            Keyword arguments for the API function

        Returns
        -------
        T
            The result of the API function

        Raises
        ------
        asyncio.TimeoutError
            If API operation times out
        Exception
            If API operation fails
        """
        config = self.get_config(operation_type)

        try:
            logger.debug(f"Executing Discord API call with timeout {config.api_timeout}s")
            return await asyncio.wait_for(api_func(*args, **kwargs), timeout=config.api_timeout)
        except TimeoutError:
            logger.error(f"Discord API call timed out after {config.api_timeout}s")
            raise
        except Exception as e:
            logger.error(f"Discord API call failed: {e}")
            raise


# Global instance for the moderation system
timeout_handler = TimeoutHandler()
