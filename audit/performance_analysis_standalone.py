#!/usr/bin/env python3
"""
Performance Analysis Tool for Tux Discord Bot (Standalone Version)

This script analyzes current performance characteristics that can be measured
without requiring a live database connection:
- Memory usage patterns and potential leaks
- Command processing bottlenecks simulation
- Response time metrics simulation
- System resource analysis

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
import psutil
from loguru import logger

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))


class PerformanceProfiler:
    """Comprehensive performance profiler for the Tux Discord bot (standalone version)."""

    def __init__(self):
        self.metrics = {
            "database_analysis": {},
            "memory_snapshots": [],
            "command_timings": [],
            "response_times": [],
            "system_resources": [],
            "bottlenecks": [],
            "code_analysis": {},
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
            # 1. Analtabase patterns from code
            await self._analyze_database_patterns()

            # 2. Measure memory usage patterns
            await self._analyze_memory_patterns()

            # 3. Identify command processing bottlenecks
            await self._identify_command_bottlenecks()

            # 4. Document response time metrics
            await self._measure_response_times()

            # 5. Analyze system resource usage
            await self._analyze_system_resources()

            # 6. Analyze codebase for performance patterns
            await self._analyze_codebase_patterns()

            # Generate final report
            report = await self._generate_report()

            return report

        finally:
            tracemalloc.stop()

    async def _analyze_database_patterns(self):
        """Analyze database usage patterns from codebase."""
        logger.info("Analyzing database usage patterns from codebase...")

        # Analyze database controller files
        db_controllers_path = Path("tux/database/controllers")
        controller_files = []

        if db_controllers_path.exists():
            controller_files = list(db_controllers_path.glob("*.py"))

        # Analyze cog files for database usage
        cogs_path = Path("tux/cogs")
        cog_files = []

        if cogs_path.exists():
            cog_files = list(cogs_path.rglob("*.py"))

        db_patterns = {
            "controller_count": len(controller_files),
            "cog_count": len(cog_files),
            "query_patterns": [],
            "potential_issues": [],
        }

        # Analyze common query patterns
        query_patterns = ["find_first", "find_many", "find_unique", "create", "update", "delete", "upsert", "count"]

        total_queries = 0
        for pattern in query_patterns:
            count = await self._count_pattern_in_files(cog_files + controller_files, pattern)
            total_queries += count
            db_patterns["query_patterns"].append({"pattern": pattern, "count": count})

        # Identify potential performance issues
        if total_queries > 100:
            db_patterns["potential_issues"].append(
                {
                    "issue": "High query count",
                    "description": f"Found {total_queries} database queries across codebase",
                    "recommendation": "Consider implementing query caching and optimization",
                }
            )

        # Check for N+1 query patterns
        n_plus_one_indicators = await self._count_pattern_in_files(cog_files, "for.*in.*find_")
        if n_plus_one_indicators > 5:
            db_patterns["potential_issues"].append(
                {
                    "issue": "Potential N+1 queries",
                    "description": f"Found {n_plus_one_indicators} potential N+1 query patterns",
                    "recommendation": "Use batch queries or includes to reduce database round trips",
                }
            )

        self.metrics["database_analysis"] = db_patterns

    async def _count_pattern_in_files(self, files: list[Path], pattern: str) -> int:
        """Count occurrences of a pattern in files."""
        count = 0
        for file_path in files:
            try:
                if file_path.name.startswith("__"):
                    continue

                async with aiofiles.open(file_path, encoding="utf-8") as f:
                    content = await f.read()
                    count += content.count(pattern)
            except Exception as e:
                logger.debug(f"Could not read {file_path}: {e}")
        return count

    async def _analyze_memory_patterns(self):
        """Measure memory usage patterns and identify potential leaks."""
        logger.info("Analyzing memory usage patterns...")

        # Take initial memory snapshot
        initial_memory = self.process.memory_info()
        gc.collect()  # Force garbage collection

        # Simulate various operations to test memory usage
        operations = [
            ("idle_baseline", self._memory_test_idle),
            ("object_creation", self._memory_test_object_creation),
            ("large_data_processing", self._memory_test_large_data),
            ("async_operations", self._memory_test_async_ops),
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

    async def _memory_test_object_creation(self):
        """Test memory usage during object creation."""
        objects = []
        for i in range(1000):
            obj = {"id": i, "data": f"test_data_{i}", "timestamp": datetime.now(UTC), "nested": {"value": i * 2}}
            objects.append(obj)

        # Clear references
        objects.clear()

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

    async def _memory_test_async_ops(self):
        """Test memory usage with async operations."""
        tasks = []
        for i in range(100):
            task = asyncio.create_task(self._async_operation(i))
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def _async_operation(self, value: int):
        """Simulate an async operation."""
        await asyncio.sleep(0.001)
        return value * 2

    async def _identify_command_bottlenecks(self):
        """Identify bottlenecks in command processing."""
        logger.info("Identifying command processing bottlenecks...")

        # Simulate command processing patterns
        command_tests = [
            ("simple_command", self._simulate_simple_command),
            ("cpu_intensive_command", self._simulate_cpu_intensive_command),
            ("io_bound_command", self._simulate_io_bound_command),
            ("complex_computation", self._simulate_complex_command),
            ("memory_intensive_command", self._simulate_memory_intensive_command),
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

    async def _simulate_cpu_intensive_command(self):
        """Simulate a CPU-intensive command."""
        # CPU-intensive operation
        data = list(range(10000))
        sorted_data = sorted(data, reverse=True)
        filtered_data = [x for x in sorted_data if x % 2 == 0]
        return len(filtered_data)

    async def _simulate_io_bound_command(self):
        """Simulate an I/O bound command."""
        # Simulate file I/O or network delay
        await asyncio.sleep(0.05)  # 50ms simulated I/O
        return "io_result"

    async def _simulate_complex_command(self):
        """Simulate a computationally complex command."""
        # Complex nested operations
        result = 0
        for i in range(1000):
            for j in range(10):
                result += i * j
        return result

    async def _simulate_memory_intensive_command(self):
        """Simulate a memory-intensive command."""
        # Create and process large data structures
        data = [[i * j for j in range(100)] for i in range(100)]
        flattened = [item for sublist in data for item in sublist]
        return sum(flattened)

    def _get_bottleneck_recommendation(self, cmd_name: str, avg_time: float) -> str:
        """Get recommendation for addressing bottleneck."""
        recommendations = {
            "cpu_intensive_command": "Consider moving heavy computation to background tasks or implementing caching",
            "io_bound_command": "Implement async I/O with connection pooling and timeout handling",
            "complex_computation": "Optimize algorithms or implement result caching",
            "memory_intensive_command": "Implement streaming processing or data pagination",
            "simple_command": "Review for unnecessary overhead or blocking operations",
        }
        return recommendations.get(cmd_name, "Review implementation for optimization opportunities")

    async def _measure_response_times(self):
        """Document current response time metrics."""
        logger.info("Measuring response time metrics...")

        # Test different response scenarios
        response_tests = [
            ("text_response", self._test_text_response),
            ("json_response", self._test_json_response),
            ("file_processing", self._test_file_processing),
            ("error_handling", self._test_error_handling),
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

    async def _test_text_response(self):
        """Test simple text response time."""
        return "Simple text response for performance testing"

    async def _test_json_response(self):
        """Test JSON response preparation time."""
        data = {
            "status": "success",
            "data": [{"id": i, "value": f"item_{i}"} for i in range(100)],
            "timestamp": datetime.now(UTC).isoformat(),
        }
        return json.dumps(data)

    async def _test_file_processing(self):
        """Test file processing time."""
        # Simulate file processing
        content = "Test file content\n" * 1000
        lines = content.split("\n")
        processed = [line.upper() for line in lines if line.strip()]
        return len(processed)

    async def _test_error_handling(self):
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
            system_disk = psutil.disk_usage("/")

            self.metrics["system_resources"].append(
                {
                    "sample": i + 1,
                    "process_cpu_percent": cpu_percent,
                    "process_memory_mb": memory_info.rss / (1024 * 1024),
                    "process_memory_vms_mb": memory_info.vms / (1024 * 1024),
                    "system_cpu_percent": system_cpu,
                    "system_memory_percent": system_memory.percent,
                    "system_memory_available_mb": system_memory.available / (1024 * 1024),
                    "system_disk_percent": system_disk.percent,
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

            await asyncio.sleep(0.5)  # Sample every 500ms

    async def _analyze_codebase_patterns(self):
        """Analyze codebase for performance-related patterns."""
        logger.info("Analyzing codebase patterns...")

        # Analyze cog files
        cogs_path = Path("tux/cogs")
        cog_files = []

        if cogs_path.exists():
            cog_files = list(cogs_path.rglob("*.py"))

        # Performance-related patterns to look for
        patterns = {
            "sync_operations": ["time.sleep", "requests.get", "requests.post"],
            "database_queries": ["find_first", "find_many", "create", "update", "delete"],
            "loops_in_commands": ["for ", "while "],
            "exception_handling": ["try:", "except:", "raise"],
            "async_patterns": ["async def", "await ", "asyncio."],
        }

        pattern_counts = {}
        for pattern_type, pattern_list in patterns.items():
            total_count = 0
            for pattern in pattern_list:
                count = await self._count_pattern_in_files(cog_files, pattern)
                total_count += count
            pattern_counts[pattern_type] = total_count

        # Analyze file sizes and complexity
        file_stats = []
        for file_path in cog_files:
            try:
                if file_path.name.startswith("__"):
                    continue

                async with aiofiles.open(file_path, encoding="utf-8") as f:
                    content = await f.read()
                    lines = content.split("\n")

                file_stats.append(
                    {
                        "file": str(file_path.relative_to(Path.cwd())),
                        "lines": len(lines),
                        "size_kb": len(content) / 1024,
                        "functions": content.count("def "),
                        "classes": content.count("class "),
                    }
                )
            except Exception as e:
                logger.debug(f"Could not analyze {file_path}: {e}")

        # Sort by lines to find largest files
        file_stats.sort(key=lambda x: x["lines"], reverse=True)

        self.metrics["code_analysis"] = {
            "total_cog_files": len(cog_files),
            "pattern_counts": pattern_counts,
            "largest_files": file_stats[:10],  # Top 10 largest files
            "average_file_size_lines": sum(f["lines"] for f in file_stats) / len(file_stats) if file_stats else 0,
            "total_functions": sum(f["functions"] for f in file_stats),
            "total_classes": sum(f["classes"] for f in file_stats),
        }

    async def _generate_report(self) -> dict[str, Any]:
        """Generate comprehensive performance report."""
        logger.info("Generating performance report...")

        # Calculate summary statistics
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
                "bottlenecks_identified": len(self.metrics["bottlenecks"]),
                "memory_tests_performed": len(memory_snapshots),
                "command_types_tested": len(command_timings),
                "cog_files_analyzed": self.metrics["code_analysis"].get("total_cog_files", 0),
            },
            "database_analysis": self.metrics["database_analysis"],
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
            "code_analysis": self.metrics["code_analysis"],
            "bottlenecks_identified": self.metrics["bottlenecks"],
            "response_time_metrics": self.metrics["response_times"],
            "recommendations": self._generate_recommendations(),
        }

        return report

    def _generate_recommendations(self) -> list[dict[str, str]]:
        """Generate performance improvement recommendations."""
        recommendations = []

        # Database recommendations
        db_analysis = self.metrics["database_analysis"]
        if db_analysis.get("potential_issues"):
            for issue in db_analysis["potential_issues"]:
                recommendations.append(
                    {
                        "category": "database",
                        "priority": "high",
                        "issue": issue["issue"],
                        "recommendation": issue["recommendation"],
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

        # Code analysis recommendations
        code_analysis = self.metrics["code_analysis"]
        sync_ops = code_analysis.get("pattern_counts", {}).get("sync_operations", 0)
        if sync_ops > 10:
            recommendations.append(
                {
                    "category": "code_quality",
                    "priority": "medium",
                    "issue": f"{sync_ops} synchronous operations found",
                    "recommendation": "Replace synchronous operations with async alternatives",
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
    logger.info("Starting Tux Discord Bot Performance Analysis (Standalone)")

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
        print(f"Cog files analyzed: {summary['cog_files_analyzed']}")
        print(f"Bottlenecks identified: {summary['bottlenecks_identified']}")

        db_analysis = report["database_analysis"]
        print("\nDatabase Analysis:")
        print(f"  Controller files: {db_analysis.get('controller_count', 0)}")
        print(f"  Cog files: {db_analysis.get('cog_count', 0)}")
        print(f"  Potential issues: {len(db_analysis.get('potential_issues', []))}")

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

        code_analysis = report["code_analysis"]
        print("\nCode Analysis:")
        print(f"  Total functions: {code_analysis.get('total_functions', 0)}")
        print(f"  Total classes: {code_analysis.get('total_classes', 0)}")
        print(f"  Average file size: {code_analysis.get('average_file_size_lines', 0):.0f} lines")

        print(f"\nRecommendations: {len(report['recommendations'])}")
        for rec in report["recommendations"]:
            print(f"  [{rec['priority'].upper()}] {rec['category']}: {rec['issue']}")

        print("\n" + "=" * 80)

        return report

    except Exception as e:
        logger.error(f"Performance analysis failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
