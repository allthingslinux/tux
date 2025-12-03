"""
Execution service for moderation operations.

Handles retry logic, circuit breakers, and execution management
using proper service composition.
"""

import asyncio
import time
from collections.abc import Callable, Coroutine
from typing import Any

import discord
from loguru import logger

from tux.database.models import CaseType as DBCaseType


class ExecutionService:
    """
    Service for executing moderation actions with retry logic.

    Provides circuit breaker patterns and proper error handling
    for Discord API operations.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        max_retries: int = 3,
        base_delay: float = 1.0,
    ):
        """
        Initialize the execution service.

        Parameters
        ----------
        failure_threshold : int, optional
            Number of failures before opening circuit breaker, by default 5.
        recovery_timeout : float, optional
            Seconds to wait before retrying after circuit opens, by default 60.0.
        max_retries : int, optional
            Maximum number of retry attempts for operations, by default 3.
        base_delay : float, optional
            Base delay in seconds for exponential backoff, by default 1.0.
        """
        # Circuit breaker state
        self._circuit_open: dict[str, bool] = {}
        self._failure_count: dict[str, int] = {}
        self._last_failure_time: dict[str, float] = {}

        # Configuration
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._max_retries = max_retries
        self._base_delay = base_delay

    async def execute_with_retry(  # noqa: PLR0912
        self,
        operation_type: str,
        action: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute an action with retry logic and circuit breaker.

        Parameters
        ----------
        operation_type : str
            Type of operation for circuit breaker.
        action : Callable[..., Coroutine[Any, Any, Any]]
            The async callable to execute (must be a callable, not a coroutine).
        *args : Any
            Positional arguments for the action.
        **kwargs : Any
            Keyword arguments for the action.

        Returns
        -------
        Any
            The result of the action.

        Raises
        ------
        RuntimeError
            If the circuit breaker is open for this operation type.
        discord.Forbidden
            If the bot lacks permissions.
        discord.HTTPException
            If a Discord API error occurs.
        discord.NotFound
            If the resource is not found.
        """
        if self._is_circuit_open(operation_type):
            msg = f"Circuit breaker open for {operation_type}"
            raise RuntimeError(msg)

        last_exception = None

        for attempt in range(self._max_retries):
            try:
                logger.debug(
                    f"Executing action for {operation_type} (attempt {attempt + 1}/{self._max_retries})",
                )
                result = await action(*args, **kwargs)
            except discord.RateLimited as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    delay = self._calculate_delay(
                        attempt,
                        e.retry_after or self._base_delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    self._record_failure(operation_type)

            except (discord.Forbidden, discord.NotFound):
                # Don't retry these errors
                self._record_failure(operation_type)
                raise

            except discord.HTTPException as e:
                last_exception = e
                if e.status >= 500:  # Server errors
                    if attempt < self._max_retries - 1:
                        delay = self._calculate_delay(attempt, self._base_delay)
                        await asyncio.sleep(delay)
                    else:
                        self._record_failure(operation_type)
                else:
                    # Client errors, don't retry
                    self._record_failure(operation_type)
                    raise

            except Exception as e:
                last_exception = e
                if attempt < self._max_retries - 1:
                    delay = self._calculate_delay(attempt, self._base_delay)
                    await asyncio.sleep(delay)
                else:
                    self._record_failure(operation_type)
            else:
                # No exception raised - success!
                self._record_success(operation_type)
                return result

        # If we get here, all retries failed
        if last_exception:
            raise last_exception
        msg = "Execution failed with unknown error"
        raise RuntimeError(msg)

    def _is_circuit_open(self, operation_type: str) -> bool:
        """
        Check if the circuit breaker is open for an operation type.

        Parameters
        ----------
        operation_type : str
            The operation type to check.

        Returns
        -------
        bool
            True if circuit is open, False otherwise.
        """
        if not self._circuit_open.get(operation_type, False):
            return False

        # Check if recovery timeout has passed
        last_failure = self._last_failure_time.get(operation_type, 0)
        if time.monotonic() - last_failure > self._recovery_timeout:
            # Reset circuit breaker
            self._circuit_open[operation_type] = False
            self._failure_count[operation_type] = 0
            return False

        return True

    def _record_success(self, operation_type: str) -> None:
        """
        Record a successful operation.

        Parameters
        ----------
        operation_type : str
            The operation type.
        """
        self._failure_count[operation_type] = 0
        self._circuit_open[operation_type] = False

    def _record_failure(self, operation_type: str) -> None:
        """
        Record a failed operation.

        Parameters
        ----------
        operation_type : str
            The operation type.
        """
        self._failure_count[operation_type] = (
            self._failure_count.get(operation_type, 0) + 1
        )

        if self._failure_count[operation_type] >= self._failure_threshold:
            self._circuit_open[operation_type] = True
            self._last_failure_time[operation_type] = time.monotonic()

    def _calculate_delay(self, attempt: int, base_delay: float) -> float:
        """
        Calculate delay for retry with exponential backoff.

        Parameters
        ----------
        attempt : int
            The current attempt number (0-based).
        base_delay : float
            Base delay in seconds.

        Returns
        -------
        float
            Delay in seconds.
        """
        # Exponential backoff with jitter
        delay = base_delay * (2**attempt)
        jitter = delay * 0.1 * (time.monotonic() % 1)  # 10% jitter
        return min(delay + jitter, 30.0)  # Cap at 30 seconds

    def get_operation_type(self, case_type: DBCaseType) -> str:
        """
        Get the operation type for circuit breaker based on case type.

        Uses the case type name directly as the operation type for simplicity
        and clear correlation between operations and their failure patterns.

        Parameters
        ----------
        case_type : DBCaseType
            The case type.

        Returns
        -------
        str
            Operation type string for circuit breaker configuration.
        """
        return case_type.value
