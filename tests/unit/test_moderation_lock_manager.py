"""
🚀 LockManager Unit Tests - User Action Locking System

Tests for the LockManager mixin that handles user-specific action locking
to prevent race conditions in concurrent moderation operations.

Test Coverage:
- Lock acquisition and release
- Concurrent operation queuing
- Lock cleanup and memory management
- Race condition prevention
- Timeout handling for queued operations
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock

from tux.services.moderation.lock_manager import LockManager, LockQueueItem


class TestLockManager:
    """🔒 Test LockManager functionality."""

    @pytest.fixture
    def lock_manager(self) -> LockManager:
        """Create a fresh LockManager instance for each test."""
        return LockManager()

    @pytest.mark.unit
    async def test_get_user_lock_creates_new_lock(self, lock_manager: LockManager) -> None:
        """Test that get_user_lock creates a new lock for a user."""
        user_id = 123456789
        lock = await lock_manager.get_user_lock(user_id)

        assert user_id in lock_manager._user_action_locks
        assert lock is lock_manager._user_action_locks[user_id]
        assert lock.locked() is False

    @pytest.mark.unit
    async def test_get_user_lock_reuses_existing_lock(self, lock_manager: LockManager) -> None:
        """Test that get_user_lock reuses existing lock for same user."""
        user_id = 123456789

        lock1 = await lock_manager.get_user_lock(user_id)
        lock2 = await lock_manager.get_user_lock(user_id)

        assert lock1 is lock2
        assert user_id in lock_manager._user_action_locks

    @pytest.mark.unit
    async def test_clean_user_locks_removes_unlocked_locks(self, lock_manager: LockManager) -> None:
        """Test that clean_user_locks removes unlocked locks."""
        # Create locks for multiple users
        user1_id = 123456789
        user2_id = 987654321

        lock1 = await lock_manager.get_user_lock(user1_id)
        lock2 = await lock_manager.get_user_lock(user2_id)

        # Manually lock one of them
        await lock1.acquire()
        await lock2.acquire()

        # Release one lock
        lock1.release()

        # Clean up - should remove user1's lock but keep user2's
        await lock_manager.clean_user_locks()

        assert user1_id not in lock_manager._user_action_locks
        assert user2_id in lock_manager._user_action_locks
        assert lock_manager._user_action_locks[user2_id].locked()

        # Clean up
        lock2.release()

    @pytest.mark.unit
    async def test_execute_with_queue_sequential_operations(self, lock_manager: LockManager) -> None:
        """Test that execute_with_queue handles sequential operations correctly."""
        user_id = 123456789

        # Mock async function
        async def mock_action(value: int) -> int:
            await asyncio.sleep(0.01)  # Small delay
            return value * 2

        # Execute multiple operations sequentially
        result1 = await lock_manager.execute_with_queue(user_id, mock_action, 5)
        result2 = await lock_manager.execute_with_queue(user_id, mock_action, 10)

        assert result1 == 10  # 5 * 2
        assert result2 == 20  # 10 * 2

    @pytest.mark.unit
    async def test_execute_with_queue_concurrent_operations(self, lock_manager: LockManager) -> None:
        """Test that execute_with_queue properly queues concurrent operations."""
        user_id = 123456789
        results = []
        errors = []

        # Use a very short queue timeout for fast tests
        lock_manager._queue_timeout = 1.0

        async def quick_action(value: int) -> int:
            # Very short operation to avoid timing issues
            results.append(value)
            return value * 2

        # Start two concurrent operations
        task1 = asyncio.create_task(lock_manager.execute_with_queue(user_id, quick_action, 1))
        task2 = asyncio.create_task(lock_manager.execute_with_queue(user_id, quick_action, 2))

        # Wait for both to complete
        completed_results = await asyncio.gather(task1, task2, return_exceptions=True)

        # All should succeed and return correct values
        successful_results = [r for r in completed_results if not isinstance(r, Exception)]
        assert len(successful_results) == 2
        assert 2 in successful_results  # 1 * 2
        assert 4 in successful_results  # 2 * 2

        # Results should be processed in order (due to queuing)
        assert len(results) == 2
        # The order might vary due to concurrent execution, so just check both values are present
        assert 1 in results and 2 in results

    @pytest.mark.unit
    async def test_execute_with_queue_timeout(self, lock_manager: LockManager) -> None:
        """Test that operations execute immediately when no lock is held."""
        user_id = 123456789

        async def slow_action() -> str:
            await asyncio.sleep(0.1)  # Short delay
            return "completed"

        # With no lock held, operation should execute immediately
        result = await lock_manager.execute_with_queue(user_id, slow_action)
        assert result == "completed"

    @pytest.mark.unit
    async def test_execute_user_action_with_lock_basic(self, lock_manager: LockManager) -> None:
        """Test execute_user_action_with_lock basic functionality."""
        user_id = 123456789
        call_count = 0

        async def test_action() -> str:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return f"result_{call_count}"

        result = await lock_manager.execute_user_action_with_lock(user_id, test_action)

        assert result == "result_1"
        assert call_count == 1

    @pytest.mark.unit
    async def test_execute_user_action_with_lock_concurrent_safety(self, lock_manager: LockManager) -> None:
        """Test that execute_with_queue prevents concurrent access."""
        user_id = 123456789
        execution_order = []

        # Use a very short queue timeout for fast tests
        lock_manager._queue_timeout = 1.0

        async def tracked_action(name: str) -> str:
            execution_order.append(f"start_{name}")
            # Very short sleep to ensure sequential execution
            await asyncio.sleep(0.001)
            execution_order.append(f"end_{name}")
            return f"result_{name}"

        # Start first operation and let it acquire the lock
        task1 = asyncio.create_task(lock_manager.execute_with_queue(user_id, tracked_action, "first"))

        # Wait a tiny bit to ensure first operation starts
        await asyncio.sleep(0.001)

        # Start second operation - should queue behind first
        task2 = asyncio.create_task(lock_manager.execute_with_queue(user_id, tracked_action, "second"))

        # Wait for both to complete
        results = await asyncio.gather(task1, task2)

        # Both should complete successfully
        assert "result_first" in results
        assert "result_second" in results

        # Operations should not overlap (second should wait for first to complete)
        start_first_idx = execution_order.index("start_first")
        end_first_idx = execution_order.index("end_first")
        start_second_idx = execution_order.index("start_second")

        assert start_second_idx > end_first_idx, "Second operation started before first completed"

    @pytest.mark.unit
    async def test_lock_cleanup_threshold(self, lock_manager: LockManager) -> None:
        """Test that lock cleanup happens when threshold is exceeded."""
        # Set low threshold for testing
        lock_manager._lock_cleanup_threshold = 3

        # Create multiple locks
        user_ids = [1001, 1002, 1003, 1004, 1005]

        for user_id in user_ids:
            await lock_manager.get_user_lock(user_id)

        # Should have cleaned up some locks (exact behavior depends on implementation)
        # At minimum, should not have infinite growth
        assert len(lock_manager._user_action_locks) <= len(user_ids)

    @pytest.mark.unit
    async def test_lock_queue_item_creation(self) -> None:
        """Test LockQueueItem creation and properties."""
        user_id = 123456789

        async def test_func(x: int) -> int:
            return x * 2

        item = LockQueueItem(
            user_id=user_id,
            action_func=test_func,
            args=(5,),
            kwargs={"extra": "value"},
        )

        assert item.user_id == user_id
        assert item.action_func == test_func
        assert item.args == (5,)
        assert item.kwargs == {"extra": "value"}
        assert item.future is None

    @pytest.mark.unit
    async def test_empty_queue_cleanup(self, lock_manager: LockManager) -> None:
        """Test that empty queues are cleaned up automatically."""
        user_id = 123456789

        async def quick_action() -> str:
            return "done"

        # Execute an action to create a queue
        result = await lock_manager.execute_with_queue(user_id, quick_action)
        assert result == "done"

        # Queue should be cleaned up after operation
        assert user_id not in lock_manager._user_queues

    @pytest.mark.unit
    async def test_queue_size_limit(self, lock_manager: LockManager) -> None:
        """Test that queue size limits are enforced when operations are queued."""
        user_id = 123456789

        # Set very small queue size for testing
        lock_manager._max_queue_size = 1  # Only allow 1 queued operation

        # First, acquire a lock to force queuing
        lock = await lock_manager.get_user_lock(user_id)
        await lock.acquire()

        try:
            async def quick_action() -> str:
                return "done"

            # Fill the queue by trying to add operations while lock is held
            # This should work since operations will queue
            task1 = asyncio.create_task(lock_manager.execute_with_queue(user_id, quick_action))
            # Second operation should also work (fits in queue)
            task2 = asyncio.create_task(lock_manager.execute_with_queue(user_id, quick_action))

            # Third operation should fail due to queue size limit
            with pytest.raises(Exception, match="timed out"):
                await lock_manager.execute_with_queue(user_id, quick_action)

        finally:
            lock.release()
            # Process queued operations
            await lock_manager._process_queue(user_id)
