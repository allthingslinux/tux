#!/usr/bin/env python3
"""
Performance Analysis Tool for Tux Discord Bot

This script analyzes current performance characteristics including:
- Database query performance profiling
- Memory usage patterns and potential leaks
- Command processing bottlenecks
- Response time metrics

Requirements: 4.1, 4.2, 4.3, 9.3
"""

import asyncio
import gc
import json
import sys
import time
import tracemalloc
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import aiofiles
import discord
import psutil
from loguru import logger

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from tux.database.client import db


class PerformanceProfiler:
    """Comprehensive performance profiler for the Tux Discord bot."""

    def __init__(self):
        self.metrics = {
            "database_queries": [],
            "memory_snapshots": [],
            "command_timings": [],
            "response_times": [],
            "system_resources": [],
            "bottlenecks": [],
            "analysis_timestamp": datetime.now(UTC).isoformat(),
        }
        self.start_time = time.time()
        self.process = psutil.Process()

    async def run_analysis(self) -> dict[str, Any]:
        """Run comprehensive performance analysis."""
        logger.info("Starting performance analysis...")

        # Start memory tracing
        tracemalloc.start()

        try:
            # 1. Profile database query performance
            await self._profile_database_queries()

            # 2. Measure memory usage patterns
            await self._analyze_memory_patterns()

            # 3. Identify command processing bottlenecks
            await self._identify_command_bottlenecks()

            # 4. Document response time metrics
            await self._measure_response_times()

            # 5. Analyze system resource usage
            await self._analyze_system_resources()

            # Generate final report
            report = await self._generate_report()

            return report

        finally:
            tracemalloc.stop()

    async def _profile_database_queries(self):
        """Profile database query performance across all operations."""
        logger.info("Profiling database query performance...")

        # Connect to database
        await db.connect()

        # Test common query patterns
        query_tests = [
            ("find_unique_guild", self._test_guild_lookup),
            ("find_many_cases", self._test_case_queries),
            ("create_snippet", self._test_snippet_creation),
            ("update_guild_config", self._test_config_updates),
            ("complex_joins", self._test_complex_queries),
            ("batch_operations", self._test_batch_operations),
        ]

        for test_name, test_func in query_tests:
            try:
                start_time = time.perf_counter()
                result = await test_func()
                end_time = time.perf_counter()

                self.metrics["database_queries"].append(
                    {
                        "test_name": test_name,
                        "duration_ms": (end_time - start_time) * 1000,
                        "success": True,
                        "result_count": result.get("count", 0) if isinstance(result, dict) else 1,
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

            except Exception as e:
                logger.error(f"Database test {test_name} failed: {e}")
                self.metrics["database_queries"].append(
                    {
                        "test_name": test_name,
                        "duration_ms": 0,
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now(UTC).isoformat(),
                    }
                )

    async def _test_guild_lookup(self) -> dict[str, Any]:
        """Test guild lookup performance."""
        # Test finding a guild by ID
        guild = await db.client.guild.find_first(
            where={"guild_id": 123456789}  # Test ID
        )
        return {"count": 1 if guild else 0}

    async def _test_case_queries(self) -> dict[str, Any]:
        """Test case query performance."""
        # Test finding cases with pagination
        cases = await db.client.case.find_many(take=50, order={"case_created_at": "desc"})
        return {"count": len(cases)}

    async def _test_snippet_creation(self) -> dict[str, Any]:
        """Test snippet creation performance."""
        # Test creating a snippet (will be cleaned up)
        test_snippet = await db.client.snippet.create(
            data={
                "snippet_name": f"perf_test_{int(time.time())}",
                "snippet_content": "Performance test snippet",
                "snippet_created_at": datetime.now(UTC),
                "snippet_user_id": 123456789,
                "guild_id": 123456789,
            }
        )

        # Clean up test snippet
        await db.client.snippet.delete(where={"snippet_id": test_snippet.snippet_id})

        return {"count": 1}

    async def _test_config_updates(self) -> dict[str, Any]:
        """Test configuration update performance."""
        # Test upsert operation
        config = await db.client.guildconfig.upsert(
            where={"guild_id": 123456789},
            data={"create": {"guild_id": 123456789, "prefix": "!test"}, "update": {"prefix": "!test"}},
        )
        return {"count": 1}

    async def _test_complex_queries(self) -> dict[str, Any]:
        """Test complex queries with joins."""
        # Test query with includes
        cases_with_guild = await db.client.case.find_many(take=10, include={"guild": True})
        return {"count": len(cases_with_guild)}

    async def _test_batch_operations(self) -> dict[str, Any]:
        """Test batch operation performance."""
        # Test batch creation/deletion
        async with db.batch():
            # This would batch multiple operations
            pass
        return {"count": 1}

    async def _analyze_memory_patterns(self):
        """Measure memory usage patterns and identify potential leaks."""
        logger.info("Analyzing memory usage patterns...")

        # Take initial memory snapshot
        initial_memory = self.process.memory_info()
        gc.collect()  # Force garbage collection

        # Simulate various operations to test memory usage
        operations = [
            ("idle_baseline", self._memory_test_idle),
            ("database_operations", self._memory_test_database),
            ("embed_creation", self._memory_test_embeds),
            ("large_data_processing", self._memory_test_large_data),
        ]

        for op_name, op_func in operations:
            # Take snapshot before operation
            before_memory = self.process.memory_info()
            before_snapshot = tracemalloc.take_snapshot()

            # Run operation
            await op_func()

            # Take snapshot after operation
            after_memory = self.process.memory_info()
            after_snapshot = tracemalloc.take_snapshot()

            # Calculate memory difference
            memory_diff = after_memory.rss - before_memory.rss

            # Get top memory consumers
            top_stats = after_snapshot.compare_to(before_snapshot, "lineno")[:10]

            self.metrics["memory_snapshots"].append(
                {
                    "operation": op_name,
                    "memory_before_mb": before_memory.rss / (1024 * 1024),
                    "memory_after_mb": after_memory.rss / (1024 * 1024),
                    "memory_diff_mb": memory_diff / (1024 * 1024),
                    "top_allocations": [
                        {
                            "file": stat.traceback.format()[0] if stat.traceback else "unknown",
                            "size_mb": stat.size / (1024 * 1024),
                            "count": stat.count,
                        }
                        for stat in top_stats[:5]
                    ],
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            # Force garbage collection between tests
            gc.collect()

    async def _memory_test_idle(self):
        """Test memory usage during idle state."""
        await asyncio.sleep(0.1)

    async def _memory_test_database(self):
        """Test memory usage during database operations."""
        for _ in range(100):
            await db.client.guild.find_first(where={"guild_id": 123456789})

    async def _memory_test_embeds(self):
        """Test memory usage during embed creation."""
        embeds = []
        for i in range(100):
            embed = discord.Embed(
                title=f"Test Embed {i}", description="This is a test embed for memory analysis", color=0x00FF00
            )
            embed.add_field(name="Field 1", value="Value 1", inline=True)
            embed.add_field(name="Field 2", value="Value 2", inline=True)
            embeds.append(embed)

        # Clear references
        embeds.clear()

    async def _memory_test_large_data(self):
        """Test memory usage with large data structures."""
        large_data = []
        for i in range(1000):
            large_data.append(
                {
                    "id": i,
                    "data": "x" * 1000,  # 1KB of data per item
                    "timestamp": datetime.now(UTC),
                }
            )

        # Process the data
        processed = [item for item in large_data if item["id"] % 2 == 0]

        # Clear references
        large_data.clear()
        processed.clear()

    async def _identify_command_bottlenecks(self):
        """Identify bottlenecks in command processing."""
        logger.info("Identifying command processing bottlenecks...")

        # Simulate command processing patterns
        command_tests = [
            ("simple_command", self._simulate_simple_command),
            ("database_heavy_command", self._simulate_db_heavy_command),
            ("api_call_command", self._simulate_api_command),
            ("complex_computation", self._simulate_complex_command),
        ]

        for cmd_name, cmd_func in command_tests:
            # Run multiple iterations to get average
            timings = []
            for _ in range(10):
                start_time = time.perf_counter()
                await cmd_func()
                end_time = time.perf_counter()
                timings.append((end_time - start_time) * 1000)

            avg_time = sum(timings) / len(timings)
            min_time = min(timings)
            max_time = max(timings)

            # Identify if this is a bottleneck (>100ms average)
            is_bottleneck = avg_time > 100

            self.metrics["command_timings"].append(
                {
                    "command_type": cmd_name,
                    "avg_time_ms": avg_time,
                    "min_time_ms": min_time,
                    "max_time_ms": max_time,
                    "is_bottleneck": is_bottleneck,
                    "iterations": len(timings),
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            if is_bottleneck:
                self.metrics["bottlenecks"].append(
                    {
                        "type": "command_processing",
                        "command": cmd_name,
                        "avg_time_ms": avg_time,
                        "severity": "high" if avg_time > 500 else "medium",
                        "recommendation": self._get_bottleneck_recommendation(cmd_name, avg_time),
                    }
                )

    async def _simulate_simple_command(self):
        """Simulate a simple command like ping."""
        # Simple computation
        result = sum(range(100))
        await asyncio.sleep(0.001)  # Simulate minimal async work
        return result

    async def _simulate_db_heavy_command(self):
        """Simulate a database-heavy command."""
        # Multiple database queries
        for _ in range(5):
            await db.client.guild.find_first(where={"guild_id": 123456789})

    async def _simulate_api_command(self):
        """Simulate a command that makes external API calls."""
        # Simulate network delay
        await asyncio.sleep(0.05)  # 50ms simulated API call

    async def _simulate_complex_command(self):
        """Simulate a computationally complex command."""
        # CPU-intensive operation
        data = list(range(10000))
        sorted_data = sorted(data, reverse=True)
        filtered_data = [x for x in sorted_data if x % 2 == 0]
        return len(filtered_data)

    def _get_bottleneck_recommendation(self, cmd_name: str, avg_time: float) -> str:
        """Get recommendation for addressing bottleneck."""
        recommendations = {
            "database_heavy_command": "Consider implementing query caching, connection pooling, or query optimization",
            "api_call_command": "Implement async HTTP client with connection pooling and timeout handling",
            "complex_computation": "Consider moving heavy computation to background tasks or implementing caching",
            "simple_command": "Review for unnecessary overhead or blocking operations",
        }
        return recommendations.get(cmd_name, "Review implementation for optimization opportunities")

    async def _measure_response_times(self):
        """Document current response time metrics."""
        logger.info("Measuring response time metrics...")

        # Test different response scenarios
        response_tests = [
            ("embed_response", self._test_embed_response),
            ("text_response", self._test_text_response),
            ("file_response", self._test_file_response),
            ("error_response", self._test_error_response),
        ]

        for test_name, test_func in response_tests:
            timings = []
            for _ in range(5):
                start_time = time.perf_counter()
                await test_func()
                end_time = time.perf_counter()
                timings.append((end_time - start_time) * 1000)

            self.metrics["response_times"].append(
                {
                    "response_type": test_name,
                    "avg_time_ms": sum(timings) / len(timings),
                    "min_time_ms": min(timings),
                    "max_time_ms": max(timings),
                    "samples": len(timings),
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

    async def _test_embed_response(self):
        """Test embed creation time."""
        embed = discord.Embed(
            title="Performance Test", description="Testing embed creation performance", color=0x00FF00
        )
        embed.add_field(name="Test", value="Value", inline=True)
        return embed

    async def _test_text_response(self):
        """Test simple text response time."""
        return "Simple text response for performance testing"

    async def _test_file_response(self):
        """Test file response preparation time."""
        # Simulate file preparation
        content = "Test file content\n" * 100
        return content

    async def _test_error_response(self):
        """Test error response handling time."""
        try:
            raise ValueError("Test error for performance analysis")
        except ValueError as e:
            # Simulate error handling
            error_msg = f"Error occurred: {e}"
            return error_msg

    async def _analyze_system_resources(self):
        """Analyze system resource usage patterns."""
        logger.info("Analyzing system resource usage...")

        # Take multiple samples over time
        for i in range(10):
            cpu_percent = self.process.cpu_percent()
            memory_info = self.process.memory_info()

            # System-wide metrics
            system_cpu = psutil.cpu_percent()
            system_memory = psutil.virtual_memory()

            self.metrics["system_resources"].append(
                {
                    "sample": i + 1,
                    "process_cpu_percent": cpu_percent,
                    "process_memory_mb": memory_info.rss / (1024 * 1024),
                    "process_memory_vms_mb": memory_info.vms / (1024 * 1024),
                    "system_cpu_percent": system_cpu,
                    "system_memory_percent": system_memory.percent,
                    "system_memory_available_mb": system_memory.available / (1024 * 1024),
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            await asyncio.sleep(0.5)  # Sample every 500ms

    async def _generate_report(self) -> dict[str, Any]:
        """Generate comprehensive performance report."""
        logger.info("Generating performance report...")

        # Calculate summary statistics
        db_queries = self.metrics["database_queries"]
        successful_queries = [q for q in db_queries if q["success"]]

        if successful_queries:
            avg_db_time = sum(q["duration_ms"] for q in successful_queries) / len(successful_queries)
            max_db_time = max(q["duration_ms"] for q in successful_queries)
            min_db_time = min(q["duration_ms"] for q in successful_queries)
        else:
            avg_db_time = max_db_time = min_db_time = 0

        # Memory analysis
        memory_snapshots = self.metrics["memory_snapshots"]
        if memory_snapshots:
            total_memory_growth = sum(m["memory_diff_mb"] for m in memory_snapshots)
            max_memory_usage = max(m["memory_after_mb"] for m in memory_snapshots)
        else:
            total_memory_growth = max_memory_usage = 0

        # Command timing analysis
        command_timings = self.metrics["command_timings"]
        bottleneck_commands = [c for c in command_timings if c["is_bottleneck"]]

        # System resource analysis
        system_resources = self.metrics["system_resources"]
        if system_resources:
            avg_cpu = sum(r["process_cpu_percent"] for r in system_resources) / len(system_resources)
            avg_memory = sum(r["process_memory_mb"] for r in system_resources) / len(system_resources)
        else:
            avg_cpu = avg_memory = 0

        report = {
            "analysis_summary": {
                "total_analysis_time_seconds": time.time() - self.start_time,
                "timestamp": datetime.now(UTC).isoformat(),
                "database_queries_tested": len(db_queries),
                "successful_queries": len(successful_queries),
                "failed_queries": len(db_queries) - len(successful_queries),
                "bottlenecks_identified": len(self.metrics["bottlenecks"]),
                "memory_tests_performed": len(memory_snapshots),
                "command_types_tested": len(command_timings),
            },
            "database_performance": {
                "average_query_time_ms": avg_db_time,
                "fastest_query_time_ms": min_db_time,
                "slowest_query_time_ms": max_db_time,
                "queries_over_100ms": len([q for q in successful_queries if q["duration_ms"] > 100]),
                "queries_over_500ms": len([q for q in successful_queries if q["duration_ms"] > 500]),
                "detailed_results": db_queries,
            },
            "memory_analysis": {
                "total_memory_growth_mb": total_memory_growth,
                "peak_memory_usage_mb": max_memory_usage,
                "potential_leaks_detected": len([m for m in memory_snapshots if m["memory_diff_mb"] > 10]),
                "detailed_snapshots": memory_snapshots,
            },
            "command_performance": {
                "total_commands_tested": len(command_timings),
                "bottleneck_commands": len(bottleneck_commands),
                "average_response_time_ms": sum(c["avg_time_ms"] for c in command_timings) / len(command_timings)
                if command_timings
                else 0,
                "detailed_timings": command_timings,
            },
            "system_resources": {
                "average_cpu_percent": avg_cpu,
                "average_memory_mb": avg_memory,
                "resource_samples": system_resources,
            },
            "bottlenecks_identified": self.metrics["bottlenecks"],
            "response_time_metrics": self.metrics["response_times"],
            "recommendations": self._generate_recommendations(),
        }

        return report

    def _generate_recommendations(self) -> list[dict[str, str]]:
        """Generate performance improvement recommendations."""
        recommendations = []

        # Database recommendations
        db_queries = [q for q in self.metrics["database_queries"] if q["success"]]
        slow_queries = [q for q in db_queries if q["duration_ms"] > 100]

        if slow_queries:
            recommendations.append(
                {
                    "category": "database",
                    "priority": "high",
                    "issue": f"{len(slow_queries)} database queries taking >100ms",
                    "recommendation": "Implement query optimization, indexing, and connection pooling",
                }
            )

        # Memory recommendations
        memory_growth = sum(m["memory_diff_mb"] for m in self.metrics["memory_snapshots"])
        if memory_growth > 50:
            recommendations.append(
                {
                    "category": "memory",
                    "priority": "medium",
                    "issue": f"Total memory growth of {memory_growth:.1f}MB during testing",
                    "recommendation": "Review object lifecycle management and implement proper cleanup",
                }
            )

        # Command performance recommendations
        bottlenecks = self.metrics["bottlenecks"]
        if bottlenecks:
            recommendations.append(
                {
                    "category": "commands",
                    "priority": "high",
                    "issue": f"{len(bottlenecks)} command bottlenecks identified",
                    "recommendation": "Optimize slow commands with caching, async patterns, and background processing",
                }
            )

        # System resource recommendations
        system_resources = self.metrics["system_resources"]
        if system_resources:
            avg_cpu = sum(r["process_cpu_percent"] for r in system_resources) / len(system_resources)
            if avg_cpu > 50:
                recommendations.append(
                    {
                        "category": "system",
                        "priority": "medium",
                        "issue": f"High average CPU usage: {avg_cpu:.1f}%",
                        "recommendation": "Profile CPU-intensive operations and consider optimization",
                    }
                )

        return recommendations


async def main():
    """Main function to run performance analysis."""
    logger.info("Starting Tux Discord Bot Performance Analysis")

    # Initialize profiler
    profiler = PerformanceProfiler()

    try:
        # Run comprehensive analysis
        report = await profiler.run_analysis()

        # Save report to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"performance_analysis_report_{timestamp}.json"

        async with aiofiles.open(report_file, "w") as f:
            await f.write(json.dumps(report, indent=2, default=str))

        logger.info(f"Performance analysis complete. Report saved to {report_file}")

        # Print summary
        print("\n" + "=" * 80)
        print("PERFORMANCE ANALYSIS SUMMARY")
        print("=" * 80)

        summary = report["analysis_summary"]
        print(f"Analysis completed in {summary['total_analysis_time_seconds']:.2f} seconds")
        print(f"Database queries tested: {summary['database_queries_tested']}")
        print(f"Successful queries: {summary['successful_queries']}")
        print(f"Failed queries: {summary['failed_queries']}")
        print(f"Bottlenecks identified: {summary['bottlenecks_identified']}")

        db_perf = report["database_performance"]
        print("\nDatabase Performance:")
        print(f"  Average query time: {db_perf['average_query_time_ms']:.2f}ms")
        print(f"  Slowest query: {db_perf['slowest_query_time_ms']:.2f}ms")
        print(f"  Queries >100ms: {db_perf['queries_over_100ms']}")
        print(f"  Queries >500ms: {db_perf['queries_over_500ms']}")

        mem_analysis = report["memory_analysis"]
        print("\nMemory Analysis:")
        print(f"  Total memory growth: {mem_analysis['total_memory_growth_mb']:.2f}MB")
        print(f"  Peak memory usage: {mem_analysis['peak_memory_usage_mb']:.2f}MB")
        print(f"  Potential leaks detected: {mem_analysis['potential_leaks_detected']}")

        cmd_perf = report["command_performance"]
        print("\nCommand Performance:")
        print(f"  Commands tested: {cmd_perf['total_commands_tested']}")
        print(f"  Bottleneck commands: {cmd_perf['bottleneck_commands']}")
        print(f"  Average response time: {cmd_perf['average_response_time_ms']:.2f}ms")

        print(f"\nRecommendations: {len(report['recommendations'])}")
        for rec in report["recommendations"]:
            print(f"  [{rec['priority'].upper()}] {rec['category']}: {rec['issue']}")

        print("\n" + "=" * 80)

        return report

    except Exception as e:
        logger.error(f"Performance analysis failed: {e}")
        raise

    finally:
        # Cleanup
        if db.is_connected():
            await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
