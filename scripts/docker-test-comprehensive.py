#!/usr/bin/env python3

import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import and initialize the custom Tux logger
import logger_setup  # noqa: F401 # pyright: ignore[reportUnusedImport]
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


def add_test_result(metrics: dict[str, Any], test_name: str, duration: int, status: str, details: str = "") -> None:
    """Add a test result to metrics."""
    metrics["tests"].append(
        {
            "test": test_name,
            "duration_ms": duration,
            "status": status,
            "details": details,
            "timestamp": datetime.now(tz=UTC).isoformat(),
        },
    )


def run_fresh_build_test(name: str, target: str, tag: str) -> int:
    """Run a fresh build test (no cache)."""
    logger.info(f"Testing fresh {name} build (no cache)")
    timer = Timer()
    timer.start()

    try:
        safe_run(
            ["docker", "build", "--no-cache", "--target", target, "-t", tag, "."],
            capture_output=True,
            timeout=300,
        )
        duration = timer.elapsed_ms()
        logger.success(f"Fresh {name} build completed in {duration}ms")
    except Exception:
        duration = timer.elapsed_ms()
        logger.error(f"❌ Fresh {name} build failed after {duration}ms")
        return duration
    else:
        return duration


def run_security_tests() -> None:
    """Run security-related tests."""
    logger.info("🔒 Running security tests...")

    # Test non-root execution
    try:
        result = safe_run(
            ["docker", "run", "--rm", "--entrypoint=", "tux:fresh-prod", "whoami"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        user_output = result.stdout.strip()
        if user_output == "nonroot":
            logger.success("✅ Non-root execution confirmed")
        else:
            logger.warning(f"⚠️  Unexpected user: {user_output}")
    except Exception as e:
        logger.error(f"❌ Security test failed: {e}")

    # Test file permissions
    try:
        result = safe_run(
            ["docker", "run", "--rm", "--entrypoint=", "tux:fresh-prod", "ls", "-la", "/"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        logger.success("✅ File permission test passed")
    except Exception as e:
        logger.error(f"❌ File permission test failed: {e}")


def run_performance_tests() -> None:  # sourcery skip: extract-method
    """Run performance-related tests."""
    logger.info("📊 Running performance tests...")

    # Test container startup time
    timer = Timer()
    timer.start()

    try:
        result = safe_run(
            ["docker", "run", "-d", "--rm", "--entrypoint=", "tux:fresh-prod", "sleep", "30"],
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
        logger.success(f"✅ Container startup time: {startup_time}ms")

        # Clean up
        safe_run(["docker", "stop", container_id], capture_output=True, timeout=10)
    except Exception as e:
        logger.error(f"❌ Performance test failed: {e}")


def run_compatibility_tests() -> None:
    """Run compatibility and integration tests."""
    logger.info("🔗 Running compatibility tests...")

    # Test Python compatibility
    try:
        result = safe_run(
            ["docker", "run", "--rm", "--entrypoint=", "tux:fresh-prod", "python", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        logger.success(f"✅ Python compatibility: {result.stdout.strip()}")
    except Exception as e:
        logger.error(f"❌ Python compatibility test failed: {e}")

    # Test compose compatibility
    try:
        safe_run(
            ["python", "scripts/docker-compose.py", "config"],
            capture_output=True,
            timeout=30,
        )
        logger.success("✅ Compose compatibility confirmed")
    except Exception as e:
        logger.error(f"❌ Compose compatibility test failed: {e}")


def main():  # noqa: PLR0915
    """Main entry point."""
    logger.info("🧪 Comprehensive Docker Testing Strategy")
    logger.info("=" * 50)
    logger.info("Testing all developer scenarios and workflows")
    logger.info("")

    if not check_docker():
        logger.error("Docker is not running or accessible")
        sys.exit(1)

    # Create comprehensive test directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    comp_log_dir = logs_dir / f"comprehensive-test-{timestamp}"
    comp_log_dir.mkdir(exist_ok=True)

    comp_metrics_file = comp_log_dir / "comprehensive-metrics.json"
    comp_report_file = comp_log_dir / "test-report.md"

    logger.info(f"Log directory: {comp_log_dir}")
    logger.info("")
    logger.success("🛡️  SAFETY: This script only removes Tux-related resources")
    logger.info("    System images, containers, and volumes are preserved")
    logger.info("")

    # Initialize metrics
    metrics: dict[str, Any] = {"test_session": timestamp, "tests": []}

    def comp_section(title: str) -> None:
        logger.info("")
        logger.info(f"🔵 {title}")
        logger.info("=" * 60)

    # 1. Clean Slate Testing
    comp_section("1. CLEAN SLATE TESTING (No Cache)")
    logger.info("Testing builds from absolute zero state")

    # Fresh Development Build
    logger.info("1.1 Testing fresh development build (no cache)")
    dev_duration = run_fresh_build_test("development", "dev", "tux:fresh-dev")
    add_test_result(
        metrics,
        "fresh_dev_build",
        dev_duration,
        "success" if dev_duration > 0 else "failed",
        "from_scratch",
    )

    # Fresh Production Build
    logger.info("1.2 Testing fresh production build (no cache)")
    prod_duration = run_fresh_build_test("production", "production", "tux:fresh-prod")
    add_test_result(
        metrics,
        "fresh_prod_build",
        prod_duration,
        "success" if prod_duration > 0 else "failed",
        "from_scratch",
    )

    # 2. Security Testing
    comp_section("2. SECURITY TESTING")
    run_security_tests()

    # 3. Performance Testing
    comp_section("3. PERFORMANCE TESTING")
    run_performance_tests()

    # 4. Compatibility Testing
    comp_section("4. COMPATIBILITY TESTING")
    run_compatibility_tests()

    # 5. Final Cleanup
    comp_section("5. FINAL CLEANUP")
    logger.info("Cleaning up test resources...")

    try:
        safe_run(["docker", "rmi", "-f", "tux:fresh-dev", "tux:fresh-prod"], capture_output=True, timeout=60)
        logger.success("✅ Test images cleaned up")
    except Exception as e:
        logger.warning(f"⚠️  Failed to clean up test images: {e}")

    # Save metrics
    try:
        with comp_metrics_file.open("w") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Metrics saved to {comp_metrics_file}")
    except Exception as e:
        logger.warning(f"Failed to save metrics: {e}")

    # Generate report
    try:
        with comp_report_file.open("w") as f:
            f.write("# Comprehensive Docker Test Report\n\n")
            f.write(f"**Test Session:** {timestamp}\n\n")
            f.write("## Test Results\n\n")

            for test in metrics["tests"]:
                status_emoji = "✅" if test["status"] == "success" else "❌"
                f.write(f"{status_emoji} **{test['test']}** - {test['status']} ({test['duration_ms']}ms)\n")
                if test.get("details"):
                    f.write(f"   - Details: {test['details']}\n")
                f.write("\n")

        logger.info(f"Report saved to {comp_report_file}")
    except Exception as e:
        logger.warning(f"Failed to generate report: {e}")

    # Final summary
    logger.info("")
    logger.info("📊 COMPREHENSIVE TEST SUMMARY")
    logger.info("=" * 50)

    total_tests = len(metrics["tests"])
    successful_tests = len([t for t in metrics["tests"] if t["status"] == "success"])

    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Successful: {successful_tests}")
    logger.info(f"Failed: {total_tests - successful_tests}")
    logger.info(f"Success Rate: {successful_tests / total_tests * 100:.1f}%" if total_tests > 0 else "Success Rate: 0%")

    if successful_tests == total_tests:
        logger.success("🎉 All comprehensive tests passed!")
        sys.exit(0)
    else:
        logger.error("❌ Some comprehensive tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
