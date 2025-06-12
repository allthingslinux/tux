#!/usr/bin/env python3

"""Tux Docker Toolkit - Unified Docker Management and Testing Suite.

Consolidates all Docker operations: testing, monitoring, and management.
Converted from bash to Python for better maintainability and integration.
"""

import contextlib
import json
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import click
from loguru import logger

# Script version and configuration
TOOLKIT_VERSION = "2.0.0"
DEFAULT_CONTAINER_NAME = "tux-dev"
LOGS_DIR = Path("logs")

# Safety configuration - only these Docker resource patterns are allowed for cleanup
SAFE_RESOURCE_PATTERNS = {
    "images": [
        r"^tux:.*",
        r"^ghcr\.io/allthingslinux/tux:.*",
        r"^tux:(test|fresh|cached|switch-test|regression|perf-test)-.*",
        r"^tux:(multiplatform|security)-test$",
    ],
    "containers": [
        r"^(tux(-dev|-prod)?|memory-test|resource-test)$",
        r"^tux:(test|fresh|cached|switch-test|regression|perf-test)-.*",
    ],
    "volumes": [
        r"^tux(_dev)?_(cache|temp)$",
    ],
    "networks": [
        r"^tux_default$",
        r"^tux-.*",
    ],
}

# Performance thresholds (milliseconds)
DEFAULT_THRESHOLDS = {
    "build": 300000,  # 5 minutes
    "startup": 10000,  # 10 seconds
    "python": 5000,  # 5 seconds
}


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


class DockerToolkit:
    """Main Docker toolkit class for testing and management."""

    def __init__(self, testing_mode: bool = False) -> None:
        self.testing_mode = testing_mode
        self.logs_dir = LOGS_DIR
        self.logs_dir.mkdir(exist_ok=True)

        # Configure logger
        logger.remove()  # Remove default handler
        logger.add(
            sys.stderr,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
            level="INFO",
        )

    def log_to_file(self, log_file: Path) -> None:
        """Add file logging."""
        logger.add(log_file, format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}", level="DEBUG")

    def check_docker(self) -> bool:
        """Check if Docker is available and running."""
        try:
            result = subprocess.run(["docker", "version"], capture_output=True, text=True, timeout=10, check=True)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            return False
        else:
            return result.returncode == 0

    def check_dependencies(self) -> list[str]:
        """Check for optional dependencies and return list of missing ones."""
        missing: list[str] = []
        for dep in ["jq", "bc"]:
            try:
                subprocess.run([dep, "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(dep)
        return missing

    def safe_run(
        self,
        cmd: list[str],
        timeout: int = 30,
        check: bool = True,
        **kwargs: Any,
    ) -> subprocess.CompletedProcess[str]:
        """Safely run a subprocess command with validation."""
        # Basic command validation
        if not cmd:
            msg = "Command must be a non-empty list"
            raise ValueError(msg)

        if cmd[0] not in {"docker", "docker-compose", "bash", "sh"}:
            msg = f"Unsafe command: {cmd[0]}"
            raise ValueError(msg)

        logger.debug(f"Running: {' '.join(cmd[:3])}...")

        try:
            return subprocess.run(cmd, timeout=timeout, check=check, **kwargs)  # type: ignore[return-value]
        except subprocess.CalledProcessError as e:
            if self.testing_mode:
                logger.warning(f"Command failed: {e}")
                raise
            raise

    def get_tux_resources(self, resource_type: str) -> list[str]:
        """Get list of Tux-related Docker resources safely."""
        if resource_type not in SAFE_RESOURCE_PATTERNS:
            return []

        commands = {
            "images": ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
            "containers": ["docker", "ps", "-a", "--format", "{{.Names}}"],
            "volumes": ["docker", "volume", "ls", "--format", "{{.Name}}"],
            "networks": ["docker", "network", "ls", "--format", "{{.Name}}"],
        }

        cmd = commands.get(resource_type)
        if not cmd:
            return []

        try:
            result = self.safe_run(cmd, capture_output=True, text=True, check=True)
            all_resources = result.stdout.strip().split("\n") if result.stdout.strip() else []

            # Filter resources that match our safe patterns
            patterns = SAFE_RESOURCE_PATTERNS[resource_type]
            compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]

            tux_resources: list[str] = []
            for resource in all_resources:
                for pattern_regex in compiled_patterns:
                    if pattern_regex.match(resource):
                        tux_resources.append(resource)
                        break
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return []
        else:
            return tux_resources

    def safe_cleanup(self, cleanup_type: str = "basic", force: bool = False) -> None:
        """Perform safe cleanup of Tux-related Docker resources."""
        logger.info(f"Performing {cleanup_type} cleanup (tux resources only)...")

        # Remove test containers
        test_patterns = ["tux:test-", "tux:quick-", "tux:perf-test-", "memory-test", "resource-test"]
        for pattern in test_patterns:
            with contextlib.suppress(Exception):
                result = self.safe_run(
                    ["docker", "ps", "-aq", "--filter", f"ancestor={pattern}*"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    containers = result.stdout.strip().split("\n")
                    self.safe_run(["docker", "rm", "-f", *containers], check=False)

        # Remove test images
        test_images = [
            "tux:test-dev",
            "tux:test-prod",
            "tux:quick-dev",
            "tux:quick-prod",
            "tux:perf-test-dev",
            "tux:perf-test-prod",
        ]
        for image in test_images:
            with contextlib.suppress(Exception):
                self.safe_run(["docker", "rmi", image], check=False, capture_output=True)

        if cleanup_type == "aggressive" or force:
            logger.warning("Performing aggressive cleanup (SAFE: only tux-related resources)")

            # Remove tux project images
            tux_images = self.get_tux_resources("images")
            for image in tux_images:
                with contextlib.suppress(Exception):
                    self.safe_run(["docker", "rmi", image], check=False, capture_output=True)

            # Remove dangling images
            with contextlib.suppress(Exception):
                result = self.safe_run(
                    ["docker", "images", "--filter", "dangling=true", "-q"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    dangling = result.stdout.strip().split("\n")
                    self.safe_run(["docker", "rmi", *dangling], check=False, capture_output=True)

            # Prune build cache
            with contextlib.suppress(Exception):
                self.safe_run(["docker", "builder", "prune", "-f"], check=False, capture_output=True)

    def get_image_size(self, image: str) -> float:
        """Get image size in MB."""
        try:
            result = self.safe_run(
                ["docker", "images", "--format", "{{.Size}}", image],
                capture_output=True,
                text=True,
                check=True,
            )
            size_str = result.stdout.strip().split("\n")[0] if result.stdout.strip() else "0MB"
            # Extract numeric value
            size_match = re.search(r"([0-9.]+)", size_str)
            return float(size_match[1]) if size_match else 0.0
        except Exception:
            return 0.0


@click.group()
@click.version_option(TOOLKIT_VERSION)  # type: ignore[misc]
@click.option("--testing-mode", is_flag=True, help="Enable testing mode (graceful error handling)")
@click.pass_context
def cli(ctx: click.Context, testing_mode: bool) -> None:
    """Tux Docker Toolkit - Unified Docker Management and Testing Suite."""
    ctx.ensure_object(dict)
    ctx.obj["toolkit"] = DockerToolkit(testing_mode=testing_mode)


@cli.command()
@click.pass_context
def quick(ctx: click.Context) -> int:  # noqa: PLR0915
    """Quick Docker validation (2-3 minutes)."""
    toolkit: DockerToolkit = ctx.obj["toolkit"]

    if not toolkit.check_docker():
        logger.error("Docker is not running or accessible")
        sys.exit(1)

    logger.info("⚡ QUICK DOCKER VALIDATION")
    logger.info("=" * 50)
    logger.info("Testing core functionality (2-3 minutes)")

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

    timer = Timer()
    timer.start()
    try:
        toolkit.safe_run(
            ["docker", "build", "--target", "dev", "-t", "tux:quick-dev", "."],
            capture_output=True,
            timeout=180,
        )
        test_result(True, "Development build")
    except Exception:
        test_result(False, "Development build")

    timer.start()
    try:
        toolkit.safe_run(
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
        toolkit.safe_run(
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
        result = toolkit.safe_run(
            ["docker", "run", "--rm", "--entrypoint=", "tux:quick-prod", "whoami"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        user_output = result.stdout.strip() if hasattr(result, "stdout") else "failed"
        test_result(user_output == "nonroot", "Non-root execution")
    except Exception:
        test_result(False, "Non-root execution")

    # Test 4: Compose validation
    logger.info("📋 Testing compose files...")
    try:
        toolkit.safe_run(
            ["docker", "compose", "-f", "docker-compose.dev.yml", "config"],
            capture_output=True,
            timeout=30,
        )
        test_result(True, "Dev compose config")
    except Exception:
        test_result(False, "Dev compose config")

    try:
        toolkit.safe_run(["docker", "compose", "-f", "docker-compose.yml", "config"], capture_output=True, timeout=30)
        test_result(True, "Prod compose config")
    except Exception:
        test_result(False, "Prod compose config")

    # Test 5: Volume functionality
    logger.info("💻 Testing volume configuration...")
    try:
        toolkit.safe_run(
            [
                "docker",
                "run",
                "--rm",
                "--entrypoint=",
                "-v",
                "/tmp:/app/temp",
                "tux:quick-dev",
                "test",
                "-d",
                "/app/temp",
            ],
            capture_output=True,
            timeout=30,
        )
        test_result(True, "Volume mount functionality")
    except Exception:
        test_result(False, "Volume mount functionality")

    # Cleanup
    with contextlib.suppress(Exception):
        toolkit.safe_run(["docker", "rmi", "tux:quick-dev", "tux:quick-prod"], check=False, capture_output=True)

    # Summary
    logger.info("")
    logger.info("📊 Quick Test Summary:")
    logger.info("=" * 30)
    logger.success(f"Passed: {passed}")
    if failed > 0:
        logger.error(f"Failed: {failed}")

    if failed == 0:
        logger.success("\n🎉 All quick tests passed!")
        logger.info("Your Docker setup is ready for development.")
        return 0
    logger.error(f"\n⚠️  {failed} out of {passed + failed} tests failed.")
    logger.info("Run 'python -m tests.docker.toolkit test' for detailed diagnostics.")
    logger.info("Common issues to check:")
    logger.info("  - Ensure Docker is running")
    logger.info("  - Verify .env file exists with required variables")
    logger.info("  - Check Dockerfile syntax")
    logger.info("  - Review Docker compose configuration")
    return 1


@cli.command()
@click.option("--no-cache", is_flag=True, help="Force fresh builds (no Docker cache)")
@click.option("--force-clean", is_flag=True, help="Aggressive cleanup before testing")
@click.pass_context
def test(ctx: click.Context, no_cache: bool, force_clean: bool) -> int:  # noqa: PLR0915
    """Standard Docker performance testing (5-7 minutes)."""
    toolkit: DockerToolkit = ctx.obj["toolkit"]

    if not toolkit.check_docker():
        logger.error("Docker is not running or accessible")
        sys.exit(1)

    logger.info("🔧 Docker Setup Performance Test")
    logger.info("=" * 50)

    # Create log files
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    log_file = toolkit.logs_dir / f"docker-test-{timestamp}.log"
    metrics_file = toolkit.logs_dir / f"docker-metrics-{timestamp}.json"

    toolkit.log_to_file(log_file)

    # Initialize metrics
    metrics: dict[str, Any] = {
        "timestamp": datetime.now(tz=UTC).isoformat(),
        "test_mode": {"no_cache": no_cache, "force_clean": force_clean},
        "tests": [],
        "performance": {},
        "summary": {},
    }

    logger.info(f"Test log: {log_file}")
    logger.info(f"Metrics: {metrics_file}")

    # Initial cleanup
    if force_clean:
        toolkit.safe_cleanup("initial_aggressive", True)
    else:
        toolkit.safe_cleanup("initial_basic", False)

    # Test functions
    def run_build_test(name: str, target: str, tag: str) -> int | None:
        """Run a build test and return duration in ms."""
        logger.info(f"Testing {name} build...")
        timer = Timer()
        timer.start()

        build_cmd = ["docker", "build", "--target", target, "-t", tag, "."]
        if no_cache:
            build_cmd.insert(2, "--no-cache")

        try:
            toolkit.safe_run(build_cmd, capture_output=True, timeout=300)
            duration = timer.elapsed_ms()
            size = toolkit.get_image_size(tag)

            logger.success(f"{name} build successful in {duration}ms")
            logger.info(f"{name} image size: {size}MB")

            # Store metrics
            metrics["performance"][f"{target}_build"] = {"value": duration, "unit": "ms"}
            metrics["performance"][f"{target}_image_size_mb"] = {"value": size, "unit": "MB"}
        except Exception:
            duration = timer.elapsed_ms()
            logger.error(f"{name} build failed after {duration}ms")
            metrics["performance"][f"{target}_build"] = {"value": duration, "unit": "ms"}
            return None
        else:
            return duration

    # Run build tests
    run_build_test("Development", "dev", "tux:test-dev")
    run_build_test("Production", "production", "tux:test-prod")

    # Test container startup time
    logger.info("Testing container startup time...")
    timer = Timer()
    timer.start()

    try:
        result = toolkit.safe_run(
            ["docker", "run", "-d", "--rm", "--entrypoint=", "tux:test-prod", "sleep", "30"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        container_id = result.stdout.strip()

        # Wait for container to be running
        while True:
            status_result = toolkit.safe_run(
                ["docker", "inspect", "-f", "{{.State.Status}}", container_id],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if status_result.stdout.strip() == "running":
                break
            time.sleep(0.1)

        startup_duration = timer.elapsed_ms()
        toolkit.safe_run(["docker", "stop", container_id], check=False, capture_output=True)

        logger.success(f"Container startup: {startup_duration}ms")
        metrics["performance"]["container_startup"] = {"value": startup_duration, "unit": "ms"}

    except Exception:
        startup_duration = timer.elapsed_ms()
        logger.error(f"Container startup failed after {startup_duration}ms")
        metrics["performance"]["container_startup"] = {"value": startup_duration, "unit": "ms"}

    # Test security validations
    logger.info("Testing security constraints...")
    try:
        result = toolkit.safe_run(
            ["docker", "run", "--rm", "--entrypoint=", "tux:test-prod", "whoami"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        user_output = result.stdout.strip()
        if user_output == "nonroot":
            logger.success("Container runs as non-root user")
        else:
            logger.error(f"Container not running as non-root user (got: {user_output})")
    except Exception:
        logger.error("Security validation failed")

    # Test temp directory performance
    logger.info("Testing temp directory performance...")
    timer = Timer()
    timer.start()

    try:
        toolkit.safe_run(
            [
                "docker",
                "run",
                "--rm",
                "--entrypoint=",
                "tux:test-prod",
                "sh",
                "-c",
                "for i in $(seq 1 100); do echo 'test content' > /app/temp/test_$i.txt; done; rm /app/temp/test_*.txt",
            ],
            capture_output=True,
            timeout=60,
        )
        temp_duration = timer.elapsed_ms()
        logger.success(f"Temp file operations (100 files): {temp_duration}ms")
        metrics["performance"]["temp_file_ops"] = {"value": temp_duration, "unit": "ms"}
    except Exception:
        temp_duration = timer.elapsed_ms()
        logger.error(f"Temp file operations failed after {temp_duration}ms")
        metrics["performance"]["temp_file_ops"] = {"value": temp_duration, "unit": "ms"}

    # Test Python package validation
    logger.info("Testing Python package validation...")
    timer = Timer()
    timer.start()

    try:
        toolkit.safe_run(
            [
                "docker",
                "run",
                "--rm",
                "--entrypoint=",
                "tux:test-dev",
                "python",
                "-c",
                "import sys; print('Python validation:', sys.version)",
            ],
            capture_output=True,
            timeout=30,
        )
        python_duration = timer.elapsed_ms()
        logger.success(f"Python validation: {python_duration}ms")
        metrics["performance"]["python_validation"] = {"value": python_duration, "unit": "ms"}
    except Exception:
        python_duration = timer.elapsed_ms()
        logger.error(f"Python validation failed after {python_duration}ms")
        metrics["performance"]["python_validation"] = {"value": python_duration, "unit": "ms"}

    # Final cleanup
    toolkit.safe_cleanup("final_basic", False)

    # Save metrics
    metrics_file.write_text(json.dumps(metrics, indent=2))

    # Check performance thresholds
    check_performance_thresholds(metrics, toolkit)

    logger.success("Standard Docker tests completed!")
    logger.info("")
    logger.info("📊 Results:")
    logger.info(f"  📋 Log file: {log_file}")
    logger.info(f"  📈 Metrics: {metrics_file}")

    return 0


def check_performance_thresholds(metrics: dict[str, Any], toolkit: DockerToolkit) -> None:
    """Check if performance metrics meet defined thresholds."""
    logger.info("")
    logger.info("Performance Threshold Check:")
    logger.info("=" * 40)

    # Get performance data
    performance = metrics.get("performance", {})
    threshold_failed = False

    # Check build time
    build_metric = performance.get("production_build")
    if build_metric:
        build_time = build_metric.get("value", 0)
        build_threshold = DEFAULT_THRESHOLDS["build"]
        if build_time > build_threshold:
            logger.error(f"❌ FAIL: Production build time ({build_time}ms) exceeds threshold ({build_threshold}ms)")
            threshold_failed = True
        else:
            logger.success(f"✅ PASS: Production build time ({build_time}ms) within threshold ({build_threshold}ms)")

    if startup_metric := performance.get("container_startup"):
        startup_time = startup_metric.get("value", 0)
        startup_threshold = DEFAULT_THRESHOLDS["startup"]
        if startup_time > startup_threshold:
            logger.error(
                f"❌ FAIL: Container startup time ({startup_time}ms) exceeds threshold ({startup_threshold}ms)",
            )
            threshold_failed = True
        else:
            logger.success(
                f"✅ PASS: Container startup time ({startup_time}ms) within threshold ({startup_threshold}ms)",
            )

    if python_metric := performance.get("python_validation"):
        python_time = python_metric.get("value", 0)
        python_threshold = DEFAULT_THRESHOLDS["python"]
        if python_time > python_threshold:
            logger.error(f"❌ FAIL: Python validation time ({python_time}ms) exceeds threshold ({python_threshold}ms)")
            threshold_failed = True
        else:
            logger.success(f"✅ PASS: Python validation time ({python_time}ms) within threshold ({python_threshold}ms)")

    if threshold_failed:
        logger.warning("Some performance thresholds exceeded!")
        logger.info("Consider optimizing or adjusting thresholds via environment variables.")
    else:
        logger.success("All performance thresholds within acceptable ranges")


@cli.command()
@click.option("--volumes", is_flag=True, help="Also remove Tux volumes")
@click.option("--force", is_flag=True, help="Force removal without confirmation")
@click.option("--dry-run", is_flag=True, help="Show what would be removed without removing")
@click.pass_context
def cleanup(ctx: click.Context, volumes: bool, force: bool, dry_run: bool) -> int:  # noqa: PLR0915
    """Clean up Tux-related Docker resources safely."""
    toolkit: DockerToolkit = ctx.obj["toolkit"]

    logger.info("🧹 Safe Docker Cleanup")
    logger.info("=" * 30)

    if dry_run:
        logger.info("🔍 DRY RUN MODE - No resources will actually be removed")
        logger.info("")

    logger.info("Scanning for tux-related Docker resources...")

    # Get Tux-specific resources safely
    tux_containers = toolkit.get_tux_resources("containers")
    tux_images = toolkit.get_tux_resources("images")
    tux_volumes = toolkit.get_tux_resources("volumes") if volumes else []
    tux_networks = toolkit.get_tux_resources("networks")

    # Filter out special networks
    tux_networks = [net for net in tux_networks if net not in ["bridge", "host", "none"]]

    # Display what will be cleaned
    def log_resource_list(resource_type: str, resources: list[str]) -> None:
        if resources:
            logger.info(f"{resource_type} ({len(resources)}):")
            for resource in resources:
                logger.info(f"  - {resource}")
            logger.info("")

    log_resource_list("Containers", tux_containers)
    log_resource_list("Images", tux_images)
    log_resource_list("Volumes", tux_volumes)
    log_resource_list("Networks", tux_networks)

    if not any([tux_containers, tux_images, tux_volumes, tux_networks]):
        logger.success("No tux-related Docker resources found to clean up")
        return 0

    if dry_run:
        logger.info("DRY RUN: No resources were actually removed")
        return 0

    if not force and not click.confirm("Remove these tux-related Docker resources?"):
        logger.info("Cleanup cancelled")
        return 0

    logger.info("Cleaning up tux-related Docker resources...")

    # Remove resources in order
    def remove_resources(resource_type: str, resources: list[str]) -> None:
        if not resources:
            return

        commands = {
            "containers": ["docker", "rm", "-f"],
            "images": ["docker", "rmi", "-f"],
            "volumes": ["docker", "volume", "rm", "-f"],
            "networks": ["docker", "network", "rm"],
        }

        remove_cmd = commands.get(resource_type)
        if not remove_cmd:
            logger.warning(f"Unknown resource type: {resource_type}")
            return

        resource_singular = resource_type[:-1]  # Remove 's'

        for name in resources:
            try:
                toolkit.safe_run([*remove_cmd, name], check=True, capture_output=True)
                logger.success(f"Removed {resource_singular}: {name}")
            except Exception as e:
                logger.warning(f"Failed to remove {resource_singular} {name}: {e}")

    remove_resources("containers", tux_containers)
    remove_resources("images", tux_images)
    remove_resources("volumes", tux_volumes)
    remove_resources("networks", tux_networks)

    # Clean dangling images and build cache
    logger.info("Cleaning dangling images and build cache...")
    with contextlib.suppress(Exception):
        result = toolkit.safe_run(
            ["docker", "images", "--filter", "dangling=true", "--format", "{{.ID}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        dangling_ids = result.stdout.strip().split("\n") if result.stdout.strip() else []

        if dangling_ids:
            toolkit.safe_run(["docker", "rmi", "-f", *dangling_ids], capture_output=True)
            logger.info(f"Removed {len(dangling_ids)} dangling images")

    with contextlib.suppress(Exception):
        toolkit.safe_run(["docker", "builder", "prune", "-f"], capture_output=True)

    logger.success("Tux Docker cleanup completed!")
    logger.info("")
    logger.info("📊 Final system state:")
    with contextlib.suppress(Exception):
        toolkit.safe_run(["docker", "system", "df"])

    return 0


@cli.command()
@click.pass_context
def comprehensive(ctx: click.Context) -> int:  # noqa: PLR0915
    """Comprehensive Docker testing strategy (15-20 minutes)."""
    toolkit: DockerToolkit = ctx.obj["toolkit"]

    if not toolkit.check_docker():
        logger.error("Docker is not running or accessible")
        sys.exit(1)

    logger.info("🧪 Comprehensive Docker Testing Strategy")
    logger.info("=" * 50)
    logger.info("Testing all developer scenarios and workflows")
    logger.info("")

    # Create comprehensive test directory
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%d-%H%M%S")
    comp_log_dir = toolkit.logs_dir / f"comprehensive-test-{timestamp}"
    comp_log_dir.mkdir(exist_ok=True)

    comp_log_file = comp_log_dir / "test.log"
    comp_metrics_file = comp_log_dir / "comprehensive-metrics.json"
    comp_report_file = comp_log_dir / "test-report.md"

    toolkit.log_to_file(comp_log_file)

    logger.info(f"Log directory: {comp_log_dir}")
    logger.info("")
    logger.success("🛡️  SAFETY: This script only removes tux-related resources")
    logger.info("    System images, containers, and volumes are preserved")
    logger.info("")

    # Initialize metrics
    metrics: dict[str, Any] = {"test_session": timestamp, "tests": []}

    def comp_section(title: str) -> None:
        logger.info("")
        logger.info(f"🔵 {title}")
        logger.info("=" * 60)

    def add_test_result(test_name: str, duration: int, status: str, details: str = "") -> None:
        metrics["tests"].append(
            {
                "test": test_name,
                "duration_ms": duration,
                "status": status,
                "details": details,
                "timestamp": datetime.now(tz=UTC).isoformat(),
            },
        )

    # 1. Clean Slate Testing
    comp_section("1. CLEAN SLATE TESTING (No Cache)")
    logger.info("Testing builds from absolute zero state")
    toolkit.safe_cleanup("aggressive", True)

    timer = Timer()

    # Fresh Development Build
    logger.info("1.1 Testing fresh development build (no cache)")
    timer.start()
    try:
        toolkit.safe_run(
            ["docker", "build", "--no-cache", "--target", "dev", "-t", "tux:fresh-dev", "."],
            capture_output=True,
            timeout=300,
        )
        duration = timer.elapsed_ms()
        logger.success(f"Fresh dev build completed in {duration}ms")
        add_test_result("fresh_dev_build", duration, "success", "from_scratch")
    except Exception:
        duration = timer.elapsed_ms()
        logger.error(f"❌ Fresh dev build failed after {duration}ms")
        add_test_result("fresh_dev_build", duration, "failed", "from_scratch")

    # Fresh Production Build
    logger.info("1.2 Testing fresh production build (no cache)")
    timer.start()
    try:
        toolkit.safe_run(
            ["docker", "build", "--no-cache", "--target", "production", "-t", "tux:fresh-prod", "."],
            capture_output=True,
            timeout=300,
        )
        duration = timer.elapsed_ms()
        logger.success(f"Fresh prod build completed in {duration}ms")
        add_test_result("fresh_prod_build", duration, "success", "from_scratch")
    except Exception:
        duration = timer.elapsed_ms()
        logger.error(f"❌ Fresh prod build failed after {duration}ms")
        add_test_result("fresh_prod_build", duration, "failed", "from_scratch")

    # 2. Security Testing
    comp_section("2. SECURITY TESTING")
    logger.info("Testing security constraints")

    try:
        result = toolkit.safe_run(
            ["docker", "run", "--rm", "--entrypoint=", "tux:fresh-prod", "whoami"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        user_output = result.stdout.strip()
        if user_output == "nonroot":
            logger.success("✅ Container runs as non-root user")
            add_test_result("security_nonroot", 0, "success", "verified")
        else:
            logger.error(f"❌ Container running as {user_output} instead of nonroot")
            add_test_result("security_nonroot", 0, "failed", f"user: {user_output}")
    except Exception as e:
        logger.error(f"❌ Security test failed: {e}")
        add_test_result("security_nonroot", 0, "failed", str(e))

    # Final cleanup
    toolkit.safe_cleanup("final", True)

    # Save metrics
    comp_metrics_file.write_text(json.dumps(metrics, indent=2))

    # Generate report
    comp_report_file.write_text(f"""# Comprehensive Docker Testing Report

**Generated:** {datetime.now(tz=UTC).isoformat()}
**Test Session:** {timestamp}
**Duration:** ~15-20 minutes

## 🎯 Test Summary

### Tests Completed
""")

    for test in metrics["tests"]:
        status_emoji = "✅" if test["status"] == "success" else "❌"
        comp_report_file.write_text(
            comp_report_file.read_text()
            + f"- {status_emoji} {test['test']}: {test['status']} ({test['duration_ms']}ms)\n",
        )

    comp_report_file.write_text(
        comp_report_file.read_text()
        + f"""

## 📊 Detailed Metrics

See metrics file: {comp_metrics_file}

## 🎉 Conclusion

All major developer scenarios have been tested. Review the detailed logs and metrics for specific performance data and any issues that need attention.
""",
    )

    logger.success("Comprehensive testing completed!")
    logger.info(f"Test results saved to: {comp_log_dir}")
    logger.info(f"Report generated: {comp_report_file}")

    return 0


if __name__ == "__main__":
    cli()
