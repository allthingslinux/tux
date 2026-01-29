"""Unit tests for TTLCache (in-memory TTL cache)."""

import time

import pytest

from tux.cache.ttl import TTLCache

pytestmark = pytest.mark.unit


class TestTTLCache:
    """TTLCache get, set, invalidate, get_or_fetch, size, clear."""

    def test_get_missing_returns_none(self) -> None:
        """Get with missing key returns None."""
        cache = TTLCache(ttl=60.0)
        assert cache.get("missing") is None

    def test_set_and_get_returns_value(self) -> None:
        """Set then get returns the same value."""
        cache = TTLCache(ttl=60.0)
        cache.set("k", "v")
        assert cache.get("k") == "v"

    def test_get_expired_returns_none_and_removes_entry(self) -> None:
        """Get when entry has expired returns None and removes the entry."""
        cache = TTLCache(ttl=0.1)
        cache.set("k", "v")
        time.sleep(0.15)
        assert cache.get("k") is None
        assert cache.get("k") is None

    def test_set_evicts_oldest_when_at_max_size(self) -> None:
        """Set when at max_size evicts oldest entry (FIFO)."""
        cache = TTLCache(ttl=60.0, max_size=2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_invalidate_key_removes_entry(self) -> None:
        """Invalidate with key removes that entry."""
        cache = TTLCache(ttl=60.0)
        cache.set("k", "v")
        cache.invalidate("k")
        assert cache.get("k") is None

    def test_invalidate_none_clears_all(self) -> None:
        """Invalidate with None clears all entries."""
        cache = TTLCache(ttl=60.0)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.invalidate()
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_invalidate_missing_key_no_op(self) -> None:
        """Invalidate with missing key does not raise."""
        cache = TTLCache(ttl=60.0)
        cache.invalidate("nonexistent")

    def test_invalidate_keys_matching_removes_matching(self) -> None:
        """invalidate_keys_matching removes entries whose key matches predicate."""
        cache = TTLCache(ttl=60.0)
        cache.set("a1", 1)
        cache.set("a2", 2)
        cache.set("b1", 3)
        removed = cache.invalidate_keys_matching(lambda k: str(k).startswith("a"))
        assert removed == 2
        assert cache.get("a1") is None
        assert cache.get("a2") is None
        assert cache.get("b1") == 3

    def test_invalidate_keys_matching_empty_returns_zero(self) -> None:
        """invalidate_keys_matching when no keys match returns 0."""
        cache = TTLCache(ttl=60.0)
        cache.set("x", 1)
        removed = cache.invalidate_keys_matching(lambda k: False)
        assert removed == 0
        assert cache.get("x") == 1

    def test_get_or_fetch_returns_cached(self) -> None:
        """get_or_fetch returns cached value when present."""
        cache = TTLCache(ttl=60.0)
        cache.set("k", "cached")
        fetch_called = []

        def fetch() -> str:
            fetch_called.append(1)
            return "fetched"

        assert cache.get_or_fetch("k", fetch) == "cached"
        assert fetch_called == []

    def test_get_or_fetch_calls_fetch_when_missing(self) -> None:
        """get_or_fetch calls fetch when key is missing and caches result."""
        cache = TTLCache(ttl=60.0)
        fetch_called = []

        def fetch() -> str:
            fetch_called.append(1)
            return "fetched"

        assert cache.get_or_fetch("k", fetch) == "fetched"
        assert fetch_called == [1]
        assert cache.get("k") == "fetched"

    def test_get_or_fetch_caches_none_and_does_not_refetch(self) -> None:
        """get_or_fetch caches None so subsequent calls return None without refetching."""
        cache = TTLCache(ttl=60.0)
        fetch_called = []

        def fetch() -> None:
            fetch_called.append(1)

        assert cache.get_or_fetch("k", fetch) is None
        assert fetch_called == [1]
        assert cache.get_or_fetch("k", fetch) is None
        assert fetch_called == [1]

    def test_size_returns_count_and_cleans_expired(self) -> None:
        """size() removes expired entries and returns current count."""
        cache = TTLCache(ttl=60.0)
        cache.set("a", 1)
        cache.set("b", 2)
        assert cache.size() == 2
        cache.invalidate("a")
        assert cache.size() == 1

    def test_size_cleans_expired_entries(self) -> None:
        """size() removes expired entries before counting."""
        cache = TTLCache(ttl=0.05)
        cache.set("a", 1)
        cache.set("b", 2)
        time.sleep(0.08)
        assert cache.size() == 0

    def test_clear_removes_all_entries(self) -> None:
        """clear() removes all entries."""
        cache = TTLCache(ttl=60.0)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.clear()
        assert cache.get("a") is None
        assert cache.get("b") is None
        assert cache.size() == 0

    def test_clear_calls_invalidate(self) -> None:
        """clear() uses invalidate() (no key)."""
        cache = TTLCache(ttl=60.0)
        cache.set("k", 1)
        cache.clear()
        assert cache.get("k") is None
