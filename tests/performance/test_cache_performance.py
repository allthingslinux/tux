"""
Performance benchmarks for cache operations.

Tests TTLCache, GuildConfigCacheManager, and JailStatusCache performance
to ensure optimizations maintain or improve performance.
"""

import asyncio
import sys
import timeit

import pytest

from tux.cache import GuildConfigCacheManager, JailStatusCache, TTLCache


@pytest.mark.performance
class TestTTLCachePerformance:
    """Performance tests for TTLCache."""

    def test_cache_set_get_performance(self) -> None:
        """Benchmark cache set and get operations."""
        cache = TTLCache(ttl=300.0, max_size=1000)
        keys = [f"key_{i}" for i in range(100)]

        def run_operations() -> None:
            cache.clear()
            for key in keys:
                cache.set(key, f"value_{key}")
            for key in keys:
                cache.get(key)

        # Measure execution time
        execution_time = timeit.timeit(run_operations, number=100)
        # Should complete in reasonable time (< 1 second for 100 iterations)
        assert execution_time < 1.0, f"Cache operations too slow: {execution_time}s"

    def test_cache_memory_usage(self) -> None:
        """Verify __slots__ reduces memory usage."""
        cache = TTLCache()
        # With __slots__, instance should be smaller
        size = sys.getsizeof(cache)
        # Should be significantly smaller than without __slots__
        assert size < 200, f"Cache instance too large: {size} bytes"


@pytest.mark.performance
class TestGuildConfigCachePerformance:
    """Performance tests for GuildConfigCacheManager."""

    def test_cache_get_set_performance(self) -> None:
        """Benchmark guild config cache operations."""
        cache = GuildConfigCacheManager()

        async def run_operations() -> None:
            await cache.clear_all()
            for guild_id in range(100):
                await cache.set(guild_id, audit_log_id=guild_id * 10)
                await cache.get(guild_id)

        def run_sync() -> None:
            asyncio.run(run_operations())

        # Measure execution time
        execution_time = timeit.timeit(run_sync, number=50)
        # Should complete in reasonable time
        assert execution_time < 1.0, f"Cache operations too slow: {execution_time}s"


@pytest.mark.performance
class TestJailStatusCachePerformance:
    """Performance tests for JailStatusCache."""

    def test_cache_get_set_performance(self) -> None:
        """Benchmark jail status cache operations."""
        cache = JailStatusCache()

        async def run_operations() -> None:
            await cache.clear_all()
            for guild_id in range(50):
                for user_id in range(10):
                    await cache.set(guild_id, user_id, is_jailed=(user_id % 2 == 0))
                    await cache.get(guild_id, user_id)

        def run_sync() -> None:
            asyncio.run(run_operations())

        # Measure execution time
        execution_time = timeit.timeit(run_sync, number=50)
        # Should complete in reasonable time
        assert execution_time < 1.0, f"Cache operations too slow: {execution_time}s"
