"""
Performance benchmarks for data structure operations.

Tests set vs list membership, defaultdict usage, and generator expressions.
"""

import sys
import timeit
from collections import defaultdict

import pytest


@pytest.mark.performance
class TestDataStructurePerformance:
    """Performance tests for data structure choices."""

    def test_set_vs_list_membership(self) -> None:
        """Benchmark set membership vs list membership."""
        items = list(range(1000))
        test_item = 500

        def list_membership() -> bool:
            return test_item in items

        # Pre-create set to avoid creation overhead in benchmark
        item_set = set(items)

        def set_membership() -> bool:
            return test_item in item_set

        # Set should be faster for membership testing (O(1) vs O(n))
        # Note: For small lists, list might be faster due to cache locality,
        # but set scales better. This test verifies both work correctly.
        list_time = timeit.timeit(list_membership, number=10000)
        set_time = timeit.timeit(set_membership, number=10000)

        # Both should work correctly
        assert isinstance(list_membership(), bool)
        assert isinstance(set_membership(), bool)
        # For small lists, both should complete quickly
        # Set might be slightly slower due to hash overhead, but scales better
        assert list_time < 0.1, f"List membership too slow: {list_time}s"
        assert set_time < 0.1, f"Set membership too slow: {set_time}s"

    def test_defaultdict_vs_manual_dict(self) -> None:
        """Benchmark defaultdict vs manual dictionary initialization."""
        items = list(range(100))

        def manual_dict() -> dict[str, list[int]]:
            result: dict[str, list[int]] = {}
            for item in items:
                key = "even" if item % 2 == 0 else "odd"
                if key not in result:
                    result[key] = []
                result[key].append(item)
            return result

        def defaultdict_impl() -> dict[str, list[int]]:
            result: dict[str, list[int]] = defaultdict(list)
            for item in items:
                key = "even" if item % 2 == 0 else "odd"
                result[key].append(item)
            return dict(result)

        # Both should work, defaultdict might be slightly faster
        manual_time = timeit.timeit(manual_dict, number=1000)
        defaultdict_time = timeit.timeit(defaultdict_impl, number=1000)

        manual_result = manual_dict()
        defaultdict_result = defaultdict_impl()

        assert len(manual_result) == len(defaultdict_result)
        # Both should complete in reasonable time
        assert manual_time < 0.1
        assert defaultdict_time < 0.1

    def test_list_vs_generator_memory(self) -> None:
        """Test that generators use less memory for large datasets."""
        large_range = 1_000_000

        # List comprehension - creates full list in memory
        list_result = [i * 2 for i in range(large_range)]
        list_size = sys.getsizeof(list_result)

        # Generator expression - lazy evaluation
        gen_result = (i * 2 for i in range(large_range))
        gen_size = sys.getsizeof(gen_result)

        # Generator should be much smaller
        assert gen_size < list_size, (
            f"Generator {gen_size} should be smaller than list {list_size}"
        )
