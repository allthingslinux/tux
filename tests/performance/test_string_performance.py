"""
Performance benchmarks for string operations.

Tests optimized string substitution functions to ensure format_map()
improvements are measurable.
"""

import timeit
from typing import TYPE_CHECKING, cast

import pytest

from tux.plugins.atl.fact import _substitute_placeholders

if TYPE_CHECKING:
    from tux.core.bot import Tux


@pytest.mark.performance
class TestStringSubstitutionPerformance:
    """Performance tests for string placeholder substitution."""

    def test_substitute_placeholders_performance(self) -> None:
        """Benchmark placeholder substitution with multiple placeholders."""

        # Mock bot for testing
        class MockBot:
            def __init__(self) -> None:
                self.guilds = [
                    type("Guild", (), {"member_count": 100})() for _ in range(10)
                ]

        bot = MockBot()
        text = "Bot: {bot_name} | Version: {bot_version} | Guilds: {guild_count} | Members: {member_count} | Prefix: {prefix}"

        def run_substitution() -> str:
            return _substitute_placeholders(cast("Tux", bot), text)

        # Measure execution time
        execution_time = timeit.timeit(run_substitution, number=1000)
        # Should complete quickly (< 0.1 seconds for 1000 iterations)
        assert execution_time < 0.1, f"String substitution too slow: {execution_time}s"

    def test_substitute_placeholders_single_placeholder(self) -> None:
        """Benchmark placeholder substitution with single placeholder."""

        class MockBot:
            def __init__(self) -> None:
                self.guilds = [
                    type("Guild", (), {"member_count": 100})() for _ in range(10)
                ]

        bot = MockBot()
        text = "Guild count: {guild_count}"

        def run_substitution() -> str:
            return _substitute_placeholders(cast("Tux", bot), text)

        # Measure execution time
        execution_time = timeit.timeit(run_substitution, number=1000)
        # Should complete quickly
        assert execution_time < 0.1, f"String substitution too slow: {execution_time}s"
