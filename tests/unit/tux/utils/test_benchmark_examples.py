"""Example benchmark tests for demonstrating pytest-benchmark functionality.

This module contains sample benchmark tests to validate performance-critical functions.
"""

from __future__ import annotations

import random
from typing import Any

import pytest


def test_string_concatenation_benchmark(benchmark: Any) -> None:
    """Benchmark string concatenation performance."""

    def string_concat() -> str:
        result = ""
        for i in range(1000):
            result += f"item{i}"
        return result

    result = benchmark(string_concat)
    assert len(result) > 0


def test_list_comprehension_benchmark(benchmark: Any) -> None:
    """Benchmark list comprehension performance."""

    def list_comp() -> list[int]:
        return [i**2 for i in range(1000)]

    result = benchmark(list_comp)
    assert len(result) == 1000


def test_dict_creation_benchmark(benchmark: Any) -> None:
    """Benchmark dictionary creation performance."""

    def dict_creation() -> dict[str, int]:
        return {f"key{i}": i**2 for i in range(100)}

    result = benchmark(dict_creation)
    assert len(result) == 100


@pytest.mark.parametrize("size", [100, 500, 1000])
def test_list_sorting_benchmark(benchmark: Any, size: int) -> None:
    """Benchmark list sorting with different sizes."""

    data = [random.randint(1, 1000) for _ in range(size)]

    def sort_list() -> list[int]:
        return sorted(data)

    result = benchmark(sort_list)
    assert len(result) == size
    assert result == sorted(data)


def test_fibonacci_benchmark(benchmark: Any) -> None:
    """Benchmark recursive fibonacci calculation."""

    def fibonacci(n: int) -> int:
        return n if n <= 1 else fibonacci(n - 1) + fibonacci(n - 2)

    # Use a smaller number to avoid excessive computation time
    result = benchmark(fibonacci, 20)
    assert result == 6765  # fibonacci(20) = 6765
