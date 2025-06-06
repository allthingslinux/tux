"""Docker commands for the Tux CLI."""

import re
import subprocess
from pathlib import Path

import click
from loguru import logger

from tux.cli.core import (
    command_registration_decorator,
    create_group,
    run_command,
)
from tux.utils.env import is_dev_mode


# Helper function moved from impl/docker.py
def _get_compose_base_cmd() -> list[str]:
    """Get the base docker compose command with appropriate -f flags."""
    base = ["docker", "compose", "-f", "docker-compose.yml"]
    if is_dev_mode():
        base.extend(["-f", "docker-compose.dev.yml"])
    return base


def _check_docker_availability() -> bool:
    """Check if Docker is available and running."""
    try:
        subprocess.run(["docker", "version"], check=True, capture_output=True, text=True, timeout=10)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False
    else:
        return True


def _get_service_name() -> str:
    """Get the appropriate service name based on the current mode."""
    return "tux"  # Both dev and prod use the same service name


def _get_tux_image_patterns() -> list[str]:
    """Get patterns for Tux-related Docker images - SAFE: specific patterns only."""
    return [
        "tux:*",  # Official tux images
        "ghcr.io/allthingslinux/tux:*",  # GitHub registry images
        "tux:test-*",  # Test images from test script
        "tux:fresh-*",  # Comprehensive test images
        "tux:cached-*",  # Comprehensive test images
        "tux:switch-test-*",  # Comprehensive test images
        "tux:regression-*",  # Comprehensive test images
        "tux:perf-test-*",  # Performance test images
        "tux:multiplatform-test",  # Multi-platform test images
        "tux:security-test",  # Security test images
    ]


def _get_tux_container_patterns() -> list[str]:
    """Get patterns for Tux-related container names - SAFE: specific patterns only."""
    return [
        "tux",  # Main container name
        "tux-dev",  # Development container
        "tux-prod",  # Production container
        "memory-test",  # Test script containers
        "resource-test",  # Test script containers
    ]


def _get_tux_volume_patterns() -> list[str]:
    """Get patterns for Tux-related volume names - SAFE: specific patterns only."""
    return [
        "tux_cache",  # Main cache volume
        "tux_temp",  # Main temp volume
        "tux_dev_cache",  # Dev cache volume
        "tux_dev_temp",  # Dev temp volume
    ]


def _get_tux_network_patterns() -> list[str]:
    """Get patterns for Tux-related network names - SAFE: specific patterns only."""
    return [
        "tux_default",  # Default compose network
        "tux-*",  # Any tux-prefixed networks
    ]


def _get_tux_resources(resource_type: str) -> list[str]:
    """Get list of Tux-related Docker resources safely."""
    try:
        if resource_type == "images":
            patterns = _get_tux_image_patterns()
            cmd = ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"]
        elif resource_type == "containers":
            patterns = _get_tux_container_patterns()
            cmd = ["docker", "ps", "-a", "--format", "{{.Names}}"]
        elif resource_type == "volumes":
            patterns = _get_tux_volume_patterns()
            cmd = ["docker", "volume", "ls", "--format", "{{.Name}}"]
        elif resource_type == "networks":
            patterns = _get_tux_network_patterns()
            cmd = ["docker", "network", "ls", "--format", "{{.Name}}"]
        else:
            return []

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        all_resources = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Filter resources that match our patterns
        tux_resources: list[str] = []
        for resource in all_resources:
            for pattern in patterns:
                # Simple pattern matching (convert * to regex-like matching)
                pattern_regex = pattern.replace("*", ".*")

                if re.match(f"^{pattern_regex}$", resource, re.IGNORECASE):
                    tux_resources.append(resource)
                    break

    except subprocess.CalledProcessError:
        return []
    else:
        return tux_resources


def _display_resource_summary(
    tux_containers: list[str],
    tux_images: list[str],
    tux_volumes: list[str],
    tux_networks: list[str],
) -> None:  # sourcery skip: extract-duplicate-method
    """Display summary of resources that will be cleaned up."""
    logger.info("Tux Resources Found for Cleanup:")
    logger.info("=" * 50)

    if tux_containers:
        logger.info(f"Containers ({len(tux_containers)}):")
        for container in tux_containers:
            logger.info(f"  - {container}")
        logger.info("")

    if tux_images:
        logger.info(f"Images ({len(tux_images)}):")
        for image in tux_images:
            logger.info(f"  - {image}")
        logger.info("")

    if tux_volumes:
        logger.info(f"Volumes ({len(tux_volumes)}):")
        for volume in tux_volumes:
            logger.info(f"  - {volume}")
        logger.info("")

    if tux_networks:
        logger.info(f"Networks ({len(tux_networks)}):")
        for network in tux_networks:
            logger.info(f"  - {network}")
        logger.info("")


def _remove_containers(containers: list[str]) -> None:
    """Remove Docker containers."""
    for container in containers:
        try:
            subprocess.run(["docker", "rm", "-f", container], check=True, capture_output=True)
            logger.info(f"Removed container: {container}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to remove container {container}: {e}")


def _remove_images(images: list[str]) -> None:
    """Remove Docker images."""
    for image in images:
        try:
            subprocess.run(["docker", "rmi", "-f", image], check=True, capture_output=True)
            logger.info(f"Removed image: {image}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to remove image {image}: {e}")


def _remove_volumes(volumes: list[str]) -> None:
    """Remove Docker volumes."""
    for volume in volumes:
        try:
            subprocess.run(["docker", "volume", "rm", "-f", volume], check=True, capture_output=True)
            logger.info(f"Removed volume: {volume}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to remove volume {volume}: {e}")


def _remove_networks(networks: list[str]) -> None:
    """Remove Docker networks."""
    for network in networks:
        try:
            subprocess.run(["docker", "network", "rm", network], check=True, capture_output=True)
            logger.info(f"Removed network: {network}")
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to remove network {network}: {e}")


# Create the docker command group
docker_group = create_group("docker", "Docker management commands")


@command_registration_decorator(docker_group, name="build")
@click.option("--no-cache", is_flag=True, help="Build without using cache.")
@click.option("--target", help="Build specific stage (dev, production).")
def build(no_cache: bool, target: str | None) -> int:
    """Build Docker images.

    Runs `docker compose build` with optional cache and target controls.
    """
    if not _check_docker_availability():
        logger.error("Docker is not available or not running. Please start Docker first.")
        return 1

    cmd = [*_get_compose_base_cmd(), "build"]
    if no_cache:
        cmd.append("--no-cache")
    if target:
        cmd.extend(["--build-arg", f"target={target}"])

    logger.info(f"Building Docker images {'without cache' if no_cache else 'with cache'}")
    return run_command(cmd)


@command_registration_decorator(docker_group, name="up")
@click.option("-d", "--detach", is_flag=True, help="Run containers in the background.")
@click.option("--build", is_flag=True, help="Build images before starting containers.")
@click.option("--watch", is_flag=True, help="Enable file watching for development (auto-sync).")
def up(detach: bool, build: bool, watch: bool) -> int:
    """Start Docker services.

    Runs `docker compose up` with various options.
    In development mode, --watch enables automatic code syncing.
    """
    if not _check_docker_availability():
        logger.error("Docker is not available or not running. Please start Docker first.")
        return 1

    cmd = [*_get_compose_base_cmd(), "up"]

    if build:
        cmd.append("--build")
    if detach:
        cmd.append("-d")

    if watch:
        if is_dev_mode():
            cmd.append("--watch")
        else:
            logger.warning("--watch is only available in development mode")

    mode = "development" if is_dev_mode() else "production"
    logger.info(f"Starting Docker services in {mode} mode")

    return run_command(cmd)


@command_registration_decorator(docker_group, name="down")
@click.option("-v", "--volumes", is_flag=True, help="Remove associated volumes.")
@click.option("--remove-orphans", is_flag=True, help="Remove containers for services not defined in compose file.")
def down(volumes: bool, remove_orphans: bool) -> int:
    """Stop Docker services.

    Runs `docker compose down` with optional cleanup.
    """
    cmd = [*_get_compose_base_cmd(), "down"]
    if volumes:
        cmd.append("--volumes")
    if remove_orphans:
        cmd.append("--remove-orphans")

    logger.info("Stopping Docker services")
    return run_command(cmd)


@command_registration_decorator(docker_group, name="logs")
@click.option("-f", "--follow", is_flag=True, help="Follow log output.")
@click.option("-n", "--tail", type=int, help="Number of lines to show from the end of the logs.")
@click.argument("service", default=None, required=False)
def logs(follow: bool, tail: int | None, service: str | None) -> int:
    """Show logs for Docker services.

    Runs `docker compose logs [service]`.
    If no service specified, shows logs for all services.
    """
    cmd = [*_get_compose_base_cmd(), "logs"]
    if follow:
        cmd.append("-f")
    if tail:
        cmd.extend(["--tail", str(tail)])
    if service:
        cmd.append(service)
    else:
        cmd.append(_get_service_name())

    return run_command(cmd)


@command_registration_decorator(docker_group, name="ps")
def ps() -> int:
    """List running Docker containers.

    Runs `docker compose ps`.
    """
    cmd = [*_get_compose_base_cmd(), "ps"]
    return run_command(cmd)


@command_registration_decorator(docker_group, name="exec")
@click.option("-it", "--interactive", is_flag=True, default=True, help="Keep STDIN open and allocate a TTY.")
@click.argument("service", default=None, required=False)
@click.argument("command", nargs=-1, required=True)
def exec_cmd(interactive: bool, service: str | None, command: tuple[str, ...]) -> int:
    """Execute a command inside a running service container.

    Runs `docker compose exec [service] [command]`.
    """
    if not command:
        logger.error("Error: No command provided to execute.")
        return 1

    service_name = service or _get_service_name()
    cmd = [*_get_compose_base_cmd(), "exec"]

    if interactive:
        cmd.append("-it")

    cmd.extend([service_name, *command])
    return run_command(cmd)


@command_registration_decorator(docker_group, name="shell")
@click.argument("service", default=None, required=False)
def shell(service: str | None) -> int:
    """Open an interactive shell in a running container.

    Equivalent to `docker compose exec [service] bash`.
    """
    service_name = service or _get_service_name()
    cmd = [*_get_compose_base_cmd(), "exec", service_name, "bash"]

    logger.info(f"Opening shell in {service_name} container")
    return run_command(cmd)


@command_registration_decorator(docker_group, name="restart")
@click.argument("service", default=None, required=False)
def restart(service: str | None) -> int:
    """Restart Docker services.

    Runs `docker compose restart [service]`.
    """
    cmd = [*_get_compose_base_cmd(), "restart"]
    if service:
        cmd.append(service)
    else:
        cmd.append(_get_service_name())

    logger.info("Restarting Docker services")
    return run_command(cmd)


@command_registration_decorator(docker_group, name="health")
def health() -> int:
    """Check health status of running Tux containers.

    Shows health check status for Tux services only.
    """
    try:
        # Get Tux container names
        tux_containers = _get_tux_resources("containers")

        if not tux_containers:
            logger.info("No Tux containers found")
            return 0

        logger.info("Tux Container Health Status:")
        logger.info("=" * 60)

        for container in tux_containers:
            # Check if container is running
            try:
                result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Status}}", container],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                status = result.stdout.strip()

                # Get health status if available
                health_result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Health.Status}}", container],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                health_status = health_result.stdout.strip() if health_result.returncode == 0 else "no health check"

                logger.info(f"Container: {container}")
                logger.info(f"  Status: {status}")
                logger.info(f"  Health: {health_status}")
                logger.info("")

            except subprocess.CalledProcessError:
                logger.info(f"Container: {container} - Unable to get status")
                logger.info("")

    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get health status: {e}")
        return 1
    else:
        return 0


@command_registration_decorator(docker_group, name="test")
@click.option("--no-cache", is_flag=True, help="Run tests without Docker cache.")
@click.option("--force-clean", is_flag=True, help="Perform aggressive cleanup before testing.")
def test(no_cache: bool, force_clean: bool) -> int:
    """Run Docker performance and functionality tests.

    Executes the comprehensive Docker test script.
    """
    if not _check_docker_availability():
        logger.error("Docker is not available or not running. Please start Docker first.")
        return 1

    test_script = Path("scripts/test-docker.sh")
    if not test_script.exists():
        logger.error("Docker test script not found at scripts/test-docker.sh")
        return 1

    cmd = ["bash", str(test_script)]
    if no_cache:
        cmd.append("--no-cache")
    if force_clean:
        cmd.append("--force-clean")

    logger.info("Running Docker tests")
    return run_command(cmd)


@command_registration_decorator(docker_group, name="cleanup")
@click.option("--volumes", is_flag=True, help="Also remove Tux volumes.")
@click.option("--force", is_flag=True, help="Force removal without confirmation.")
@click.option("--dry-run", is_flag=True, help="Show what would be removed without actually removing.")
def cleanup(volumes: bool, force: bool, dry_run: bool) -> int:
    """Clean up Tux-related Docker resources (images, containers, networks).

    SAFETY: Only removes Tux-related resources, never affects other projects.
    """
    logger.info("Scanning for Tux-related Docker resources...")

    # Get Tux-specific resources
    tux_containers = _get_tux_resources("containers")
    tux_images = _get_tux_resources("images")
    tux_volumes = _get_tux_resources("volumes") if volumes else []
    tux_networks = _get_tux_resources("networks")

    # Filter out special items
    tux_images = [img for img in tux_images if not img.endswith("<none>:<none>")]
    tux_networks = [net for net in tux_networks if net not in ["bridge", "host", "none"]]

    if not any([tux_containers, tux_images, tux_volumes, tux_networks]):
        logger.info("No Tux-related Docker resources found to clean up")
        return 0

    # Show what will be removed
    _display_resource_summary(tux_containers, tux_images, tux_volumes, tux_networks)

    if dry_run:
        logger.info("DRY RUN: No resources were actually removed")
        return 0

    if not force:
        click.confirm("Remove these Tux-related Docker resources?", abort=True)

    logger.info("Cleaning up Tux-related Docker resources...")

    # Remove resources in order
    _remove_containers(tux_containers)
    _remove_images(tux_images)
    _remove_volumes(tux_volumes)
    _remove_networks(tux_networks)

    logger.info("Tux Docker cleanup completed")
    return 0


@command_registration_decorator(docker_group, name="config")
def config() -> int:
    """Validate and display the Docker Compose configuration.

    Runs `docker compose config` to show the resolved configuration.
    """
    cmd = [*_get_compose_base_cmd(), "config"]
    return run_command(cmd)


@command_registration_decorator(docker_group, name="pull")
def pull() -> int:
    """Pull the latest Tux images from the registry.

    Runs `docker compose pull` to update Tux images only.
    """
    cmd = [*_get_compose_base_cmd(), "pull"]
    logger.info("Pulling latest Tux Docker images")
    return run_command(cmd)
