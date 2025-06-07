"""Docker commands for the Tux CLI."""

import re
import shlex
import subprocess
from pathlib import Path
from typing import Any

import click
from loguru import logger

from tux.cli.core import (
    command_registration_decorator,
    create_group,
    run_command,
)
from tux.utils.env import is_dev_mode

# Resource configuration for safe Docker cleanup operations
RESOURCE_MAP = {
    "images": {
        "cmd": ["docker", "images", "--format", "{{.Repository}}:{{.Tag}}"],
        "regex": [
            r"^tux:.*",
            r"^ghcr\.io/allthingslinux/tux:.*",
            r"^tux:(test|fresh|cached|switch-test|regression|perf-test)-.*",
            r"^tux:(multiplatform|security)-test$",
        ],
        "remove": ["docker", "rmi", "-f"],
    },
    "containers": {
        "cmd": ["docker", "ps", "-a", "--format", "{{.Names}}"],
        "regex": [r"^(tux(-dev|-prod)?|memory-test|resource-test)$"],
        "remove": ["docker", "rm", "-f"],
    },
    "volumes": {
        "cmd": ["docker", "volume", "ls", "--format", "{{.Name}}"],
        "regex": [r"^tux(_dev)?_(cache|temp)$"],
        "remove": ["docker", "volume", "rm", "-f"],
    },
    "networks": {
        "cmd": ["docker", "network", "ls", "--format", "{{.Name}}"],
        "regex": [r"^tux_default$", r"^tux-.*"],
        "remove": ["docker", "network", "rm"],
    },
}

# Security: Allowlisted Docker commands to prevent command injection
ALLOWED_DOCKER_COMMANDS = {
    "docker",
    "images",
    "ps",
    "volume",
    "network",
    "ls",
    "rm",
    "rmi",
    "inspect",
    "version",
    "--format",
    "--filter",
    "-a",
    "-f",
}


def _validate_docker_command(cmd: list[str]) -> bool:
    """Validate that a Docker command contains only allowed components."""
    for component in cmd:
        # Allow Docker format strings like {{.Repository}}:{{.Tag}}
        if component.startswith("{{") and component.endswith("}}"):
            continue
        # Allow common Docker flags and arguments
        if component.startswith("-"):
            continue
        # Check against allowlist
        if component not in ALLOWED_DOCKER_COMMANDS and component not in [
            "{{.Repository}}:{{.Tag}}",
            "{{.Names}}",
            "{{.Name}}",
            "{{.State.Status}}",
            "{{.State.Health.Status}}",
        ]:
            msg = f"Potentially unsafe Docker command component: {component}"
            logger.warning(msg)
            return False
    return True


def _sanitize_resource_name(name: str) -> str:
    """Sanitize resource names to prevent command injection."""
    # Only allow alphanumeric characters, hyphens, underscores, dots, colons, and slashes
    # This covers valid Docker image names, container names, etc.
    if not re.match(r"^[a-zA-Z0-9._:/-]+$", name):
        msg = f"Invalid resource name format: {name}"
        raise ValueError(msg)
    return name


def _safe_subprocess_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Safely run subprocess with validation and escaping.

    Security measures:
    - Validates command structure and components
    - Uses allowlist for Docker commands
    - Sanitizes resource names to prevent injection
    - Enforces timeout and explicit error checking
    """
    # Validate command structure
    if not cmd:
        msg = "Command must be a non-empty list"
        raise ValueError(msg)

    # Log command for security audit (sanitized)
    logger.debug(f"Executing command: {shlex.join(cmd[:3])}...")

    # For Docker commands, validate against allowlist
    if cmd[0] == "docker" and not _validate_docker_command(cmd):
        msg = f"Unsafe Docker command blocked: {cmd[0]} {cmd[1] if len(cmd) > 1 else ''}"
        logger.error(msg)
        raise ValueError(msg)

    # Sanitize resource names in the command (arguments after flags)
    sanitized_cmd: list[str] = []
    for i, component in enumerate(cmd):
        if i > 2 and not component.startswith("-") and not component.startswith("{{"):
            # This is likely a resource name - sanitize it
            try:
                sanitized_cmd.append(_sanitize_resource_name(component))
            except ValueError as e:
                logger.warning(f"Resource name sanitization failed: {e}")
                # If sanitization fails, use shlex.quote as fallback
                sanitized_cmd.append(shlex.quote(component))
        else:
            sanitized_cmd.append(component)

    # Execute with timeout and capture, ensure check is explicit
    final_kwargs = {**kwargs, "timeout": kwargs.get("timeout", 30)}
    if "check" not in final_kwargs:
        final_kwargs["check"] = True

    # Extract check flag to avoid duplicate parameter
    check_flag = final_kwargs.pop("check", True)

    try:
        return subprocess.run(sanitized_cmd, check=check_flag, **final_kwargs)  # type: ignore[return-value]
    except subprocess.CalledProcessError as e:
        logger.error(
            f"Command failed with exit code {e.returncode}: {shlex.join(sanitized_cmd[:3])}...",
        )
        raise


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
        _safe_subprocess_run(["docker", "version"], capture_output=True, text=True, timeout=10)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False
    else:
        return True


def _get_service_name() -> str:
    """Get the appropriate service name based on the current mode."""
    return "tux"  # Both dev and prod use the same service name


def _get_tux_resources(resource_type: str) -> list[str]:
    """Get list of Tux-related Docker resources safely using data-driven approach."""
    cfg = RESOURCE_MAP.get(resource_type)
    if not cfg:
        return []

    try:
        result = _safe_subprocess_run(cfg["cmd"], capture_output=True, text=True, check=True)
        all_resources = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Filter resources that match our regex patterns
        tux_resources: list[str] = []
        # Compile patterns to regex objects once for better performance
        compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in cfg["regex"]]
        for resource in all_resources:
            for pattern_regex in compiled_patterns:
                if pattern_regex.match(resource):
                    tux_resources.append(resource)
                    break

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return []
    else:
        return tux_resources


def _log_resource_list(resource_type: str, resources: list[str]) -> None:
    """Log a list of resources with proper formatting."""
    if resources:
        logger.info(f"{resource_type} ({len(resources)}):")
        for resource in resources:
            logger.info(f"  - {resource}")
        logger.info("")


def _display_resource_summary(
    tux_containers: list[str],
    tux_images: list[str],
    tux_volumes: list[str],
    tux_networks: list[str],
) -> None:
    """Display summary of resources that will be cleaned up."""
    logger.info("Tux Resources Found for Cleanup:")
    logger.info("=" * 50)

    _log_resource_list("Containers", tux_containers)
    _log_resource_list("Images", tux_images)
    _log_resource_list("Volumes", tux_volumes)
    _log_resource_list("Networks", tux_networks)


def _remove_resources(resource_type: str, resources: list[str]) -> None:
    """Remove Docker resources safely using data-driven approach."""
    if not resources:
        return

    cfg = RESOURCE_MAP.get(resource_type)
    if not cfg:
        logger.warning(f"Unknown resource type: {resource_type}")
        return

    remove_cmd = cfg["remove"]
    resource_singular = resource_type[:-1]  # Remove 's' from plural

    for name in resources:
        try:
            cmd = [*remove_cmd, name]
            _safe_subprocess_run(cmd, check=True, capture_output=True)
            logger.info(f"Removed {resource_singular}: {name}")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.warning(f"Failed to remove {resource_singular} {name}: {e}")


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
    # No else clause - if no service specified, show logs for all services

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
                result = _safe_subprocess_run(
                    ["docker", "inspect", "--format", "{{.State.Status}}", container],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                status = result.stdout.strip()

                # Get health status if available
                health_result = _safe_subprocess_run(
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

    Executes the unified Docker toolkit script.
    """
    if not _check_docker_availability():
        logger.error("Docker is not available or not running. Please start Docker first.")
        return 1

    test_script = Path("scripts/docker-toolkit.sh")
    if not test_script.exists():
        logger.error("Docker toolkit script not found at scripts/docker-toolkit.sh")
        return 1

    cmd = ["bash", str(test_script), "test"]
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

    # Remove resources in order using data-driven approach
    _remove_resources("containers", tux_containers)
    _remove_resources("images", tux_images)
    _remove_resources("volumes", tux_volumes)
    _remove_resources("networks", tux_networks)

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
