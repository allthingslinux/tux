#!/usr/bin/env python3
"""
Metrics Dashboard Generator
Creates real-time dashboards for tracking codebase improvement metrics
"""

import json
import os
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class MetricSnapshot:
    timestamp: datetime
    metric_name: str
    value: float
    target: float
    status: str
    trend: str


class MetricsDashboard:
    def __init__(self, db_path: str = "metrics.db"):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize the metrics database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    target REAL NOT NULL,
                    status TEXT NOT NULL,
                    trend TEXT NOT NULL
                )
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_metric_timestamp
                ON metrics(metric_name, timestamp)
            """)

    def collect_code_quality_metrics(self) -> dict[str, float]:
        """Collect code quality metrics from various tools"""
        metrics = {}

        # Test coverage
        try:
            result = subprocess.run(["coverage", "report", "--format=json"], capture_output=True, text=True, check=True)
            coverage_data = json.loads(result.stdout)
            metrics["test_coverage"] = coverage_data["totals"]["percent_covered"]
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            metrics["test_coverage"] = 0.0

        # Code complexity
        try:
            result = subprocess.run(["radon", "cc", "tux", "--json"], capture_output=True, text=True, check=True)
            complexity_data = json.loads(result.stdout)

            total_complexity = 0
            function_count = 0

            for file_data in complexity_data.values():
                for item in file_data:
                    if item["type"] == "function":
                        total_complexity += item["complexity"]
                        function_count += 1

            metrics["avg_complexity"] = total_complexity / function_count if function_count > 0 else 0
        except (subprocess.CalledProcessError, json.JSONDecodeError, ZeroDivisionError):
            metrics["avg_complexity"] = 0.0

        # Code duplication
        try:
            result = subprocess.run(
                ["python", "scripts/detect_duplication.py"], capture_output=True, text=True, check=True
            )
            duplication_data = json.loads(result.stdout)
            metrics["duplication_percentage"] = duplication_data.get("duplication_rate", 0.0)
        except (subprocess.CalledProcessError, json.JSONDecodeError):
            metrics["duplication_percentage"] = 0.0

        # Type coverage
        try:
            result = subprocess.run(
                ["mypy", "tux", "--json-report", "/tmp/mypy-report"], check=False, capture_output=True, text=True
            )
            if os.path.exists("/tmp/mypy-report/index.json"):
                with open("/tmp/mypy-report/index.json") as f:
                    mypy_data = json.load(f)
                    metrics["type_coverage"] = mypy_data.get("percent_typed", 0.0)
            else:
                metrics["type_coverage"] = 0.0
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
            metrics["type_coverage"] = 0.0

        return metrics

    def collect_performance_metrics(self) -> dict[str, float]:
        """Collect performance metrics"""
        metrics = {}

        # Load performance test results if available
        perf_file = "performance_results.json"
        if os.path.exists(perf_file):
            try:
                with open(perf_file) as f:
                    perf_data = json.load(f)

                metrics["avg_response_time"] = perf_data.get("avg_response_time", 0.0)
                metrics["p95_response_time"] = perf_data.get("p95_response_time", 0.0)
                metrics["error_rate"] = perf_data.get("error_rate", 0.0)
                metrics["memory_usage"] = perf_data.get("memory_usage_mb", 0.0)

            except (json.JSONDecodeError, KeyError):
                pass

        # Default values if no performance data available
        for key in ["avg_response_time", "p95_response_time", "error_rate", "memory_usage"]:
            if key not in metrics:
                metrics[key] = 0.0

        return metrics

    def collect_testing_metrics(self) -> dict[str, float]:
        """Collect testing-related metrics"""
        metrics = {}

        # Test execution time
        try:
            result = subprocess.run(["pytest", "--collect-only", "-q"], capture_output=True, text=True, check=True)
            # Parse test count from output
            lines = result.stdout.strip().split("\n")
            for line in lines:
                if "tests collected" in line:
                    test_count = int(line.split()[0])
                    metrics["test_count"] = test_count
                    break
            else:
                metrics["test_count"] = 0
        except (subprocess.CalledProcessError, ValueError):
            metrics["test_count"] = 0

        # Test reliability (flaky test rate)
        flaky_tests_file = "flaky_tests.json"
        if os.path.exists(flaky_tests_file):
            try:
                with open(flaky_tests_file) as f:
                    flaky_data = json.load(f)
                    total_tests = metrics.get("test_count", 1)
                    flaky_count = len(flaky_data.get("flaky_tests", []))
                    metrics["flaky_test_rate"] = (flaky_count / total_tests) * 100 if total_tests > 0 else 0
            except (json.JSONDecodeError, KeyError):
                metrics["flaky_test_rate"] = 0.0
        else:
            metrics["flaky_test_rate"] = 0.0

        return metrics

    def store_metrics(self, metrics: dict[str, float], targets: dict[str, float]):
        """Store collected metrics in database"""
        timestamp = datetime.now()

        with sqlite3.connect(self.db_path) as conn:
            for metric_name, value in metrics.items():
                target = targets.get(metric_name, 0.0)
                status = self._calculate_status(metric_name, value, target)
                trend = self._calculate_trend(metric_name, value)

                conn.execute(
                    """
                    INSERT INTO metrics (timestamp, metric_name, value, target, status, trend)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (timestamp.isoformat(), metric_name, value, target, status, trend),
                )

    def _calculate_status(self, metric_name: str, value: float, target: float) -> str:
        """Calculate status based on metric value and target"""
        # Define metric-specific logic
        if metric_name in ["test_coverage", "type_coverage"]:
            if value >= target:
                return "excellent"
            if value >= target * 0.9:
                return "good"
            return "needs_improvement"

        if metric_name in ["avg_complexity", "duplication_percentage", "error_rate", "flaky_test_rate"]:
            if value <= target:
                return "excellent"
            if value <= target * 1.2:
                return "good"
            return "needs_improvement"

        if metric_name in ["avg_response_time", "p95_response_time"]:
            if value <= target:
                return "excellent"
            if value <= target * 1.1:
                return "good"
            return "needs_improvement"

        # Default logic
        return "good"

    def _calculate_trend(self, metric_name: str, current_value: float) -> str:
        """Calculate trend by comparing with previous values"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT value FROM metrics
                WHERE metric_name = ?
                ORDER BY timestamp DESC
                LIMIT 5 OFFSET 1
            """,
                (metric_name,),
            )

            previous_values = [row[0] for row in cursor.fetchall()]

        if len(previous_values) < 2:
            return "stable"

        avg_previous = sum(previous_values) / len(previous_values)
        change_percent = ((current_value - avg_previous) / avg_previous) * 100 if avg_previous != 0 else 0

        # Define trend thresholds
        if abs(change_percent) < 2:
            return "stable"
        if change_percent > 0:
            # For metrics where higher is better
            if metric_name in ["test_coverage", "type_coverage", "test_count"]:
                return "improving"
            return "declining"
        # For metrics where lower is better
        if metric_name in ["test_coverage", "type_coverage", "test_count"]:
            return "declining"
        return "improving"

    def generate_dashboard_data(self) -> dict[str, Any]:
        """Generate data for dashboard visualization"""
        with sqlite3.connect(self.db_path) as conn:
            # Get latest metrics
            cursor = conn.execute("""
                SELECT metric_name, value, target, status, trend, timestamp
                FROM metrics m1
                WHERE timestamp = (
                    SELECT MAX(timestamp)
                    FROM metrics m2
                    WHERE m2.metric_name = m1.metric_name
                )
                ORDER BY metric_name
            """)

            latest_metrics = []
            for row in cursor.fetchall():
                latest_metrics.append(
                    {
                        "name": row[0],
                        "value": row[1],
                        "target": row[2],
                        "status": row[3],
                        "trend": row[4],
                        "timestamp": row[5],
                    }
                )

            # Get historical data for trends
            cursor = conn.execute(
                """
                SELECT metric_name, timestamp, value
                FROM metrics
                WHERE timestamp >= ?
                ORDER BY metric_name, timestamp
            """,
                ((datetime.now() - timedelta(days=30)).isoformat(),),
            )

            historical_data = {}
            for row in cursor.fetchall():
                metric_name = row[0]
                if metric_name not in historical_data:
                    historical_data[metric_name] = []
                historical_data[metric_name].append({"timestamp": row[1], "value": row[2]})

        return {
            "latest_metrics": latest_metrics,
            "historical_data": historical_data,
            "generated_at": datetime.now().isoformat(),
            "summary": self._generate_summary(latest_metrics),
        }

    def _generate_summary(self, metrics: list[dict]) -> dict[str, Any]:
        """Generate summary statistics"""
        total_metrics = len(metrics)
        excellent_count = sum(1 for m in metrics if m["status"] == "excellent")
        good_count = sum(1 for m in metrics if m["status"] == "good")
        improving_count = sum(1 for m in metrics if m["trend"] == "improving")

        return {
            "total_metrics": total_metrics,
            "excellent_percentage": (excellent_count / total_metrics) * 100 if total_metrics > 0 else 0,
            "good_or_better_percentage": ((excellent_count + good_count) / total_metrics) * 100
            if total_metrics > 0
            else 0,
            "improving_percentage": (improving_count / total_metrics) * 100 if total_metrics > 0 else 0,
            "overall_status": self._calculate_overall_status(metrics),
        }

    def _calculate_overall_status(self, metrics: list[dict]) -> str:
        """Calculate overall project status"""
        if not metrics:
            return "unknown"

        excellent_count = sum(1 for m in metrics if m["status"] == "excellent")
        good_count = sum(1 for m in metrics if m["status"] == "good")
        total_count = len(metrics)

        excellent_ratio = excellent_count / total_count
        good_or_better_ratio = (excellent_count + good_count) / total_count

        if excellent_ratio >= 0.8:
            return "excellent"
        if good_or_better_ratio >= 0.7:
            return "good"
        return "needs_improvement"


def main():
    """Main function to collect and store metrics"""
    dashboard = MetricsDashboard()

    # Define targets for each metric
    targets = {
        "test_coverage": 90.0,
        "type_coverage": 95.0,
        "avg_complexity": 10.0,
        "duplication_percentage": 5.0,
        "avg_response_time": 200.0,
        "p95_response_time": 500.0,
        "error_rate": 1.0,
        "memory_usage": 512.0,
        "flaky_test_rate": 1.0,
    }

    # Collect all metrics
    print("Collecting code quality metrics...")
    quality_metrics = dashboard.collect_code_quality_metrics()

    print("Collecting performance metrics...")
    performance_metrics = dashboard.collect_performance_metrics()

    print("Collecting testing metrics...")
    testing_metrics = dashboard.collect_testing_metrics()

    # Combine all metrics
    all_metrics = {**quality_metrics, **performance_metrics, **testing_metrics}

    # Store metrics
    print("Storing metrics...")
    dashboard.store_metrics(all_metrics, targets)

    # Generate dashboard data
    print("Generating dashboard data...")
    dashboard_data = dashboard.generate_dashboard_data()

    # Save dashboard data to file
    with open("dashboard_data.json", "w") as f:
        json.dump(dashboard_data, f, indent=2)

    print("Dashboard data saved to dashboard_data.json")
    print(f"Overall status: {dashboard_data['summary']['overall_status']}")
    print(f"Metrics with excellent status: {dashboard_data['summary']['excellent_percentage']:.1f}%")


if __name__ == "__main__":
    main()
