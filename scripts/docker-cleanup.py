#!/usr/bin/env python3

import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import and initialize the custom Tux logger
import logger_setup  # noqa: F401 # pyright: ignore[reportUnusedImport]
from loguru import logger


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


def get_tux_resources(resource_type: str) -> list[str]:
    """Get Tux-related Docker resources safely."""
    safe_patterns: dict[str, list[str]] = {
        "images": [
            r"^tux:.*",
            r"^ghcr\.io/allthingslinux/tux:.*",
        ],
        "containers": [
            r"^(tux(-dev|-prod)?|memory-test|resource-test)$",
        ],
        "volumes": [
            r"^tux(_dev)?_(cache|temp)$",
        ],
        "networks": [
            r"^tux_default$",
            r"^tux-.*",
        ],
    }

    try:
        if resource_type == "images":
            result = safe_run(
                ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
                capture_output=True,
                text=True,
            )
        elif resource_type == "containers":
            result = safe_run(
                ["docker", "ps", "-a", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
            )
        elif resource_type == "volumes":
            result = safe_run(
                ["docker", "volume", "ls", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
            )
        elif resource_type == "networks":
            result = safe_run(
                ["docker", "network", "ls", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
            )
        else:
            return []

        stdout_content = result.stdout or ""
        resources: list[str] = [line.strip() for line in stdout_content.strip().split("\n") if line.strip()]

        # Filter by safe patterns
        safe_resources: list[str] = []
        for resource in resources:
            for pattern in safe_patterns.get(resource_type, []):
                if re.match(pattern, resource):
                    safe_resources.append(resource)
                    break
    except Exception:
        return []
    else:
        return safe_resources


def remove_resources(resource_type: str, resources: list[str]) -> None:
    """Remove Docker resources safely."""
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
            safe_run([*remove_cmd, name], capture_output=True)
            logger.success(f"Removed {resource_singular}: {name}")
        except Exception as e:
            logger.warning(f"Failed to remove {resource_singular} {name}: {e}")


def cleanup_dangling_resources() -> None:
    """Clean up dangling Docker resources."""
    logger.info("Cleaning dangling images and build cache...")

    try:
        # Remove dangling images
        result = safe_run(
            ["docker", "images", "--filter", "dangling=true", "--format", "{{.ID}}"],
            capture_output=True,
            text=True,
        )
        stdout_content = result.stdout or ""
        if dangling_ids := [line.strip() for line in stdout_content.strip().split("\n") if line.strip()]:
            safe_run(
                ["docker", "rmi", "-f", *dangling_ids],
                capture_output=True,
                text=True,
            )
            logger.success(f"Removed {len(dangling_ids)} dangling images")
        else:
            logger.info("No dangling images found")
    except Exception as e:
        logger.warning(f"Failed to clean dangling images: {e}")

    try:
        # System prune
        safe_run(["docker", "system", "prune", "-f"], capture_output=True, timeout=60)
        logger.success("System prune completed")
    except Exception as e:
        logger.warning(f"System prune failed: {e}")


def main():
    """Main entry point."""
    logger.info("🧹 Safe Docker Cleanup")
    logger.info("=" * 30)

    if not check_docker():
        logger.error("Docker is not running or accessible")
        sys.exit(1)

    # Parse command line arguments
    volumes = "--volumes" in sys.argv
    force = "--force" in sys.argv
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        logger.info("🔍 DRY RUN MODE - No resources will actually be removed")
        logger.info("")

    logger.info("Scanning for Tux-related Docker resources...")

    # Get Tux-specific resources safely
    tux_containers = get_tux_resources("containers")
    tux_images = get_tux_resources("images")
    tux_volumes = get_tux_resources("volumes") if volumes else []
    tux_networks = get_tux_resources("networks")

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
        logger.success("No Tux-related Docker resources found to clean up")
        return 0

    if dry_run:
        logger.info("DRY RUN: No resources were actually removed")
        return 0

    if not force:
        logger.warning("⚠️  This will remove Tux-related Docker resources")
        logger.info("Use --force to skip confirmation")
        return 0

    logger.info("Cleaning up Tux-related Docker resources...")

    # Remove resources in order
    remove_resources("containers", tux_containers)
    remove_resources("images", tux_images)
    remove_resources("volumes", tux_volumes)
    remove_resources("networks", tux_networks)

    # Clean up dangling resources
    cleanup_dangling_resources()

    logger.success("Tux Docker cleanup completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
