#!/usr/bin/env python3
"""Quick Docker validation tests for Tux."""

import subprocess
import sys
import time
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


def run_quick_tests() -> tuple[int, int]:
    """Run quick Docker validation tests."""
    passed = 0
    failed = 0

    def test_result(success: bool, description: str) -> None:
        nonlocal passed, failed
        if success:
            logger.success(f"✅ {description}")
            passed += 1
        else:
            logger.error(f"❌ {description}")
            failed += 1

    # Test 1: Basic builds
    logger.info("🔨 Testing builds...")

    # Development build
    timer = Timer()
    timer.start()
    try:
        safe_run(
            ["docker", "build", "--target", "dev", "-t", "tux:quick-dev", "."],
            capture_output=True,
            timeout=180,
        )
        test_result(True, "Development build")
    except Exception:
        test_result(False, "Development build")

    # Production build
    timer.start()
    try:
        safe_run(
            ["docker", "build", "--target", "production", "-t", "tux:quick-prod", "."],
            capture_output=True,
            timeout=180,
        )
        test_result(True, "Production build")
    except Exception:
        test_result(False, "Production build")

    # Test 2: Container execution
    logger.info("🏃 Testing container execution...")
    try:
        safe_run(
            ["docker", "run", "--rm", "--entrypoint=", "tux:quick-prod", "python", "--version"],
            capture_output=True,
            timeout=30,
        )
        test_result(True, "Container execution")
    except Exception:
        test_result(False, "Container execution")

    # Test 3: Security basics
    logger.info("🔒 Testing security...")
    try:
        result: subprocess.CompletedProcess[str] = safe_run(
            ["docker", "run", "--rm", "--entrypoint=", "tux:quick-prod", "whoami"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        user_output: str = result.stdout.strip()
        test_result(user_output == "nonroot", "Non-root execution")
    except Exception:
        test_result(False, "Non-root execution")

    # Test 4: Compose validation
    logger.info("📋 Testing compose files...")
    try:
        safe_run(
            ["docker", "compose", "-f", "docker-compose.dev.yml", "config"],
            capture_output=True,
            timeout=30,
        )
        test_result(True, "Compose validation")
    except Exception:
        test_result(False, "Compose validation")

    return passed, failed


def main():
    """Main entry point."""
    logger.info("⚡ QUICK DOCKER VALIDATION")
    logger.info("=" * 50)
    logger.info("Testing core functionality (2-3 minutes)")

    if not check_docker():
        logger.error("Docker is not running or accessible")
        sys.exit(1)

    passed, failed = run_quick_tests()

    # Summary
    logger.info("")
    logger.info("📊 QUICK TEST SUMMARY")
    logger.info("=" * 30)
    logger.info(f"✅ Passed: {passed}")
    logger.info(f"❌ Failed: {failed}")
    logger.info(
        f"📈 Success Rate: {passed / (passed + failed) * 100:.1f}%" if passed + failed > 0 else "📈 Success Rate: 0%",
    )

    if failed > 0:
        logger.error("❌ Some tests failed")
        sys.exit(1)
    else:
        logger.success("🎉 All quick tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
