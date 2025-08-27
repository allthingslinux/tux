#!/usr/bin/env python3

import json
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from loguru import logger


class Timer:
    """Simple timer for measuring durations."""

    def __init__(self) -> None:
        self.start_time: float | None = None

    def start(self) -> None:
        """Start the timer."""
        self.start_time = time.time()

    def elapsed_ms(self) -> int:
        """Get elapsed time in milliseconds."""
        if self.start_time is None:
            return 0
        return int((time.time() - self.start_time) * 1000)


def check_docker() -> bool:
    """Check if Docker is available and running."""
    try:
        result = subprocess.run(["docker", "version"], capture_output=True, text=True, timeout=10, check=True)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False
    else:
        return result.returncode == 0


def safe_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Safely run a command with error handling."""
    try:
        return subprocess.run(cmd, **kwargs, check=True)  # type: ignore[return-value]
    except subprocess.CalledProcessError:
        logger.error(f"Command failed: {' '.join(cmd)}")
        raise


def get_image_size(tag: str) -> float:
    """Get Docker image size in MB."""
    try:
        result = safe_run(
            ["docker", "images", "--format", "{{.Size}}", tag],
            capture_output=True,
            text=True,
        )
        if size_str := result.stdout.strip():
            if size_match := re.search(r"([0-9.]+)", size_str):
                size = float(size_match[1])
                # Convert GB to MB if needed
                if "GB" in size_str:
                    size *= 1024
                return size
            return 0.0
    except Exception:
        return 0.0
    else:
        return 0.0


def run_build_test(name: str, target: str, tag: str, no_cache: bool = False) -> int | None:
    """Run a build test and return duration in ms."""
    logger.info(f"Testing {name} build...")
    timer = Timer()
    timer.start()

    build_cmd = ["docker", "build", "--target", target, "-t", tag, "."]
    if no_cache:
        build_cmd.insert(2, "--no-cache")

    try:
        safe_run(build_cmd, capture_output=True, timeout=300)
        duration = timer.elapsed_ms()
        size = get_image_size(tag)

        logger.success(f"{name} build successful in {duration}ms")
        logger.info(f"{name} image size: {size:.1f}MB")
    except Exception:
        duration = timer.elapsed_ms()
        logger.error(f"{name} build failed after {duration}ms")
        return None
    else:
        return duration


def run_startup_test() -> int | None:
    """Test container startup time."""
    logger.info("Testing container startup time...")
    timer = Timer()
    timer.start()

    try:
        result = safe_run(
            ["docker", "run", "-d", "--rm", "--entrypoint=", "tux:test-prod", "sleep", "30"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        container_id = result.stdout.strip()

        # Wait for container to be running
        while True:
            status_result = safe_run(
                ["docker", "inspect", "-f", "{{.State.Status}}", container_id],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if status_result.stdout.strip() == "running":
                break
            time.sleep(0.1)

        startup_time = timer.elapsed_ms()
        logger.success(f"Container startup time: {startup_time}ms")

        # Clean up
        safe_run(["docker", "stop", container_id], capture_output=True, timeout=10)
    except Exception:
        startup_time = timer.elapsed_ms()
        logger.error(f"Container startup test failed after {startup_time}ms")
        return None
    else:
        return startup_time


def run_performance_tests(no_cache: bool = False) -> dict[str, Any]:
    """Run all performance tests."""
    metrics: dict[str, Any] = {
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "test_mode": {"no_cache": no_cache},
        "performance": {},
        "summary": {},
    }

    # Run build tests
    dev_duration = run_build_test("Development", "dev", "tux:test-dev", no_cache)
    prod_duration = run_build_test("Production", "production", "tux:test-prod", no_cache)

    if dev_duration:
        metrics["performance"]["dev_build"] = {"value": dev_duration, "unit": "ms"}
    if prod_duration:
        metrics["performance"]["prod_build"] = {"value": prod_duration, "unit": "ms"}

    # Test container startup time
    if startup_time := run_startup_test():
        metrics["performance"]["startup"] = {"value": startup_time, "unit": "ms"}

    # Performance thresholds
    thresholds = {
        "dev_build": 300000,  # 5 minutes
        "prod_build": 300000,  # 5 minutes
        "startup": 10000,  # 10 seconds
    }

    # Check thresholds
    logger.info("")
    logger.info("📊 PERFORMANCE THRESHOLDS")
    logger.info("=" * 40)

    all_within_thresholds = True
    for test_name, threshold in thresholds.items():
        if test_name in metrics["performance"]:
            value = metrics["performance"][test_name]["value"]
            if value <= threshold:
                logger.success(f"✅ {test_name}: {value}ms (≤ {threshold}ms)")
            else:
                logger.error(f"❌ {test_name}: {value}ms (> {threshold}ms)")
                all_within_thresholds = False
        else:
            logger.warning(f"⚠️  {test_name}: Test failed, no data")

    metrics["summary"]["all_within_thresholds"] = all_within_thresholds
    return metrics


def main():
    """Main entry point."""
    logger.info("🔧 Docker Setup Performance Test")
    logger.info("=" * 50)

    if not check_docker():
        logger.error("Docker is not running or accessible")
        sys.exit(1)

    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create log files
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    log_file = logs_dir / f"docker-test-{timestamp}.log"
    metrics_file = logs_dir / f"docker-metrics-{timestamp}.json"

    logger.info(f"Test log: {log_file}")
    logger.info(f"Metrics: {metrics_file}")

    # Run tests
    metrics = run_performance_tests()

    # Save metrics
    try:
        with metrics_file.open("w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Metrics saved to {metrics_file}")
    except Exception as e:
        logger.warning(f"Failed to save metrics: {e}")

    # Final summary
    logger.info("")
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 30)

    if metrics["summary"]["all_within_thresholds"]:
        logger.success("🎉 All performance thresholds within acceptable ranges")
        sys.exit(0)
    else:
        logger.error("❌ Some performance thresholds exceeded")
        sys.exit(1)


if __name__ == "__main__":
    main()
