"""
Lock management for moderation actions.

Handles user-specific locks to prevent race conditions in concurrent moderation operations.
Includes queuing system for handling concurrent operations on the same user.
"""

import asyncio
from asyncio import Lock, Queue
from collections.abc import Callable, Coroutine
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Any

from loguru import logger


@dataclass
class LockQueueItem:
    """Item in the lock queue for concurrent operations."""

    user_id: int
    action_func: Callable[..., Coroutine[Any, Any, Any]]
    args: tuple[Any, ...] = field(default_factory=tuple)
    kwargs: dict[str, Any] = field(default_factory=dict)
    future: asyncio.Future[Any] | None = None


class LockManager:
    """
    Manages locks for user-specific moderation actions to prevent race conditions.

    This mixin provides functionality to:
    - Create user-specific locks
    - Clean up unused locks automatically
    - Execute actions with proper locking
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

        # Dictionary to store locks per user
        self._user_action_locks: dict[int, Lock] = {}
        self._user_queues: dict[int, Queue[LockQueueItem]] = {}
        self._active_operations: dict[int, int] = {}  # user_id -> count
        # Threshold to trigger cleanup of unused user locks
        self._lock_cleanup_threshold: int = 100
        self._max_queue_size: int = 10  # Max queued operations per user
        self._queue_timeout: float = 30.0  # Max time to wait in queue

    async def get_user_lock(self, user_id: int) -> Lock:
        """
        Get or create a lock for operations on a specific user.

        If the number of stored locks exceeds the cleanup threshold, unused locks are removed.

        Parameters
        ----------
        user_id : int
            The ID of the user to get a lock for.

        Returns
        -------
        Lock
            The lock for the user.
        """
        # Cleanup check
        if len(self._user_action_locks) > self._lock_cleanup_threshold:
            await self.clean_user_locks()

        if user_id not in self._user_action_locks:
            self._user_action_locks[user_id] = Lock()
        return self._user_action_locks[user_id]

    async def clean_user_locks(self) -> None:
        """
        Remove locks for users that are not currently in use.

        Iterates through the locks and removes any that are not currently locked.
        Uses double-checking to prevent race conditions.
        """
        # Create a list of user_ids to avoid RuntimeError for changing dict size during iteration.
        unlocked_users: list[int] = []
        unlocked_users.extend(user_id for user_id, lock in self._user_action_locks.items() if not lock.locked())
        removed_count = 0
        for user_id in unlocked_users:
            # Double-check the lock is still unlocked (prevents race condition)
            if user_id in self._user_action_locks and not self._user_action_locks[user_id].locked():
                del self._user_action_locks[user_id]
                removed_count += 1

        if removed_count > 0:
            remaining_locks = len(self._user_action_locks)
            logger.debug(f"Cleaned up {removed_count} unused user action locks. {remaining_locks} locks remaining.")

    async def execute_with_queue(
        self,
        user_id: int,
        action_func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute an action with proper queuing for concurrent operations.

        If another operation is already running on this user, this operation
        will be queued and executed when the previous one completes.

        Parameters
        ----------
        user_id : int
            The ID of the user the action is being performed on
        action_func : Callable
            The async function to execute
        *args : Any
            Positional arguments for the function
        **kwargs : Any
            Keyword arguments for the function

        Returns
        -------
        R
            The result of the action function

        Raises
        ------
        Exception
            If the operation times out or fails
        """
        # Check if we can execute immediately (no lock held)
        lock = await self.get_user_lock(user_id)
        if not lock.locked():
            # Execute immediately with lock
            async with lock:
                result = await action_func(*args, **kwargs)
                # Process any queued operations after completion
                await self._process_queue(user_id)
                return result

        # Lock is held, need to queue
        if user_id not in self._user_queues:
            self._user_queues[user_id] = Queue(maxsize=self._max_queue_size)

        queue = self._user_queues[user_id]

        # Create queue item
        future: asyncio.Future[Any] = asyncio.Future()
        item = LockQueueItem(user_id=user_id, action_func=action_func, args=args, kwargs=kwargs, future=future)

        try:
            # Try to add to queue
            await asyncio.wait_for(queue.put(item), timeout=self._queue_timeout)
            logger.debug(f"Queued operation for user {user_id}, queue size: {queue.qsize()}")

            # Wait for our turn and execution
            result = await asyncio.wait_for(future, timeout=self._queue_timeout)
        except TimeoutError:
            logger.warning(f"Queue operation timed out for user {user_id}")
            # Remove from queue if possible
            if not queue.empty():
                with suppress(asyncio.QueueEmpty):
                    queue.get_nowait()
            msg = f"Operation queued for user {user_id} timed out"
            raise RuntimeError(msg) from None
        else:
            return result

    async def _process_queue(self, user_id: int) -> None:
        """
        Process the queue for a specific user.

        This should be called after completing an operation to process
        any queued operations for the same user.
        """
        if user_id not in self._user_queues:
            return

        queue = self._user_queues[user_id]

        while not queue.empty():
            try:
                item = queue.get_nowait()

                # Execute the queued operation with lock
                try:
                    lock = await self.get_user_lock(user_id)
                    async with lock:
                        result = await item.action_func(*item.args, **item.kwargs)
                        if item.future and not item.future.done():
                            item.future.set_result(result)
                except Exception as e:
                    if item.future and not item.future.done():
                        item.future.set_exception(e)

                queue.task_done()

            except asyncio.QueueEmpty:
                break

        # Clean up empty queue
        if queue.empty():
            del self._user_queues[user_id]

    async def execute_user_action_with_lock(
        self,
        user_id: int,
        action_func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Execute an action on a user with a lock to prevent race conditions.

        Parameters
        ----------
        user_id : int
            The ID of the user to lock.
        action_func : Callable[..., Coroutine[Any, Any, R]]
            The coroutine function to execute.
        *args : Any
            Arguments to pass to the function.
        **kwargs : Any
            Keyword arguments to pass to the function.

        Returns
        -------
        R
            The result of the action function.
        """
        lock = await self.get_user_lock(user_id)

        async with lock:
            return await action_func(*args, **kwargs)
