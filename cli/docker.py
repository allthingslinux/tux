"""Docker commands for the Tux CLI."""

import re
import subprocess
from pathlib import Path
from typing import Any

import click
from loguru import logger
from utils.env import is_dev_mode

from cli.core import (
    command_registration_decorator,
    create_group,
    run_command,
)

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
# Note: Only covers the first few command components (docker, compose, subcommand)
# Resource names and other arguments are validated separately
ALLOWED_DOCKER_COMMANDS = {
    "docker",
    "compose",
    "images",
    "ps",
    "volume",
    "network",
    "ls",
    "rm",
    "rmi",
    "inspect",
    "version",
    "build",
    "up",
    "down",
    "logs",
    "exec",
    "restart",
    "pull",
    "config",
    "bash",
    "sh",
    # Additional common Docker subcommands
    "container",
    "image",
    "system",
    "stats",
    "create",
    "start",
    "stop",
    "kill",
    "pause",
    "unpause",
    "rename",
    "update",
    "wait",
    "cp",
    "diff",
    "export",
    "import",
    "commit",
    "save",
    "load",
    "tag",
    "push",
    "connect",
    "disconnect",
    "prune",
    "info",
}


def _log_warning_and_return_false(message: str) -> bool:
    """Log a warning message and return False."""
    logger.warning(message)
    return False


def _validate_docker_command(cmd: list[str]) -> bool:
    """Validate that a Docker command contains only allowed components."""
    # Define allowed Docker format strings for security
    allowed_format_strings = {
        "{{.Repository}}:{{.Tag}}",
        "{{.Names}}",
        "{{.Name}}",
        "{{.State.Status}}",
        "{{.State.Health.Status}}",
        "{{.Repository}}",
        "{{.Tag}}",
        "{{.ID}}",
        "{{.Image}}",
        "{{.Command}}",
        "{{.CreatedAt}}",
        "{{.Status}}",
        "{{.Ports}}",
        "{{.Size}}",
    }

    for i, component in enumerate(cmd):
        # Validate Docker format strings more strictly
        if component.startswith("{{") and component.endswith("}}"):
            # Updated regex to allow colons, hyphens, and other valid format string characters
            if component not in allowed_format_strings and not re.match(r"^\{\{\.[\w.:-]+\}\}$", component):
                return _log_warning_and_return_false(f"Unsafe Docker format string: {component}")
            continue
        # Allow common Docker flags and arguments
        if component.startswith("-"):
            continue
        # First few components should be in allowlist (docker, compose, subcommand)
        if i <= 2 and component not in ALLOWED_DOCKER_COMMANDS:
            return _log_warning_and_return_false(f"Potentially unsafe Docker command component: {component}")
        # For later components (arguments), apply more permissive validation
        # These will be validated by _sanitize_resource_name() if they're resource names
        if i > 2:
            # Skip validation for compose file names, service names, and other dynamic values
            # These will be validated by the resource name sanitizer if appropriate
            continue
    return True


def _sanitize_resource_name(name: str) -> str:
    """Sanitize resource names to prevent command injection.

    Supports valid Docker resource naming patterns:
    - Container names: alphanumeric, underscore, period, hyphen
    - Image names: registry/namespace/repository:tag format
    - Network names: alphanumeric with separators
    - Volume names: alphanumeric with separators
    """
    # Enhanced regex to support Docker naming conventions
    # Includes support for:
    # - Registry hosts (docker.io, localhost:5000)
    # - Namespaces and repositories (library/ubuntu, myorg/myapp)
    # - Tags and digests (ubuntu:20.04, ubuntu@sha256:...)
    # - Local names (my-container, my_volume)
    if not re.match(r"^[a-zA-Z0-9]([a-zA-Z0-9._:@/-]*[a-zA-Z0-9])?$", name):
        msg = f"Invalid resource name format: {name}. Must be valid Docker resource name."
        raise ValueError(msg)

    # Additional security checks
    if len(name) > 255:  # Docker limit
        msg = f"Resource name too long: {len(name)} chars (max 255)"
        raise ValueError(msg)

    # Prevent obviously malicious patterns
    dangerous_patterns = [
        r"^\$",  # Variable expansion
        r"[;&|`]",  # Command separators and substitution
        r"\.\./",  # Path traversal
        r"^-",  # Flag injection
        r"\s",  # Whitespace
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, name):
            msg = f"Resource name contains unsafe pattern: {name}"
            raise ValueError(msg)

    return name


def _get_resource_name_commands() -> set[tuple[str, ...]]:
    """Get the set of Docker commands that use resource names as arguments."""
    return {
        ("docker", "run"),
        ("docker", "exec"),
        ("docker", "inspect"),
        ("docker", "rm"),
        ("docker", "rmi"),
        ("docker", "stop"),
        ("docker", "start"),
        ("docker", "logs"),
        ("docker", "create"),
        ("docker", "kill"),
        ("docker", "pause"),
        ("docker", "unpause"),
        ("docker", "rename"),
        ("docker", "update"),
        ("docker", "wait"),
        ("docker", "cp"),
        ("docker", "diff"),
        ("docker", "export"),
        ("docker", "import"),
        ("docker", "commit"),
        ("docker", "save"),
        ("docker", "load"),
        ("docker", "tag"),
        ("docker", "push"),
        ("docker", "pull"),
        ("docker", "volume", "inspect"),
        ("docker", "volume", "rm"),
        ("docker", "network", "inspect"),
        ("docker", "network", "rm"),
        ("docker", "network", "connect"),
        ("docker", "network", "disconnect"),
    }


def _validate_command_structure(cmd: list[str]) -> None:
    """Validate basic command structure and safety."""
    if not cmd:
        msg = "Command must be a non-empty list"
        raise ValueError(msg)

    if cmd[0] not in {"docker"}:
        msg = f"Command validation failed: unsupported executable '{cmd[0]}'"
        raise ValueError(msg)


def _sanitize_command_arguments(cmd: list[str]) -> list[str]:
    """Sanitize command arguments, validating resource names where applicable."""
    resource_name_commands = _get_resource_name_commands()

    # Determine if this command uses resource names
    cmd_key = tuple(cmd[:3]) if len(cmd) >= 3 else tuple(cmd[:2]) if len(cmd) >= 2 else tuple(cmd)
    uses_resource_names = any(cmd_key[: len(pattern)] == pattern for pattern in resource_name_commands)

    sanitized_cmd: list[str] = []

    for i, component in enumerate(cmd):
        if _should_skip_component(i, component):
            sanitized_cmd.append(component)
        elif _should_validate_as_resource_name(i, component, uses_resource_names):
            sanitized_cmd.append(_validate_and_sanitize_resource(component))
        else:
            sanitized_cmd.append(component)

    return sanitized_cmd


def _should_skip_component(index: int, component: str) -> bool:
    """Check if a component should be skipped during validation."""
    return index < 2 or component.startswith(("-", "{{"))


def _should_validate_as_resource_name(index: int, component: str, uses_resource_names: bool) -> bool:
    """Check if a component should be validated as a resource name."""
    return (
        uses_resource_names
        and not component.startswith(("-", "{{"))
        and index >= 2
        and component not in ALLOWED_DOCKER_COMMANDS
    )


def _validate_and_sanitize_resource(component: str) -> str:
    """Validate and sanitize a resource name component."""
    try:
        return _sanitize_resource_name(component)
    except ValueError as e:
        logger.error(f"Resource name validation failed and cannot be sanitized: {e}")
        msg = f"Unsafe resource name rejected: {component}"
        raise ValueError(msg) from e


def _prepare_subprocess_kwargs(kwargs: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    """Prepare kwargs for subprocess execution."""
    final_kwargs = {**kwargs, "timeout": kwargs.get("timeout", 30)}
    if "check" not in final_kwargs:
        final_kwargs["check"] = True

    check_flag = final_kwargs.pop("check", True)
    return final_kwargs, check_flag


def _safe_subprocess_run(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
    """Safely run subprocess with validation and escaping.

    Security measures:
    - Validates command structure and components
    - Uses allowlist for Docker commands
    - Sanitizes resource names to prevent injection
    - Enforces timeout and explicit error checking
    """
    # Validate command structure and safety
    _validate_command_structure(cmd)

    # Log command for security audit (sanitized)
    logger.debug(f"Executing command: {' '.join(cmd[:3])}...")

    # For Docker commands, validate against allowlist
    if cmd[0] == "docker" and not _validate_docker_command(cmd):
        msg = f"Unsafe Docker command blocked: {cmd[0]} {cmd[1] if len(cmd) > 1 else ''}"
        logger.error(msg)
        raise ValueError(msg)

    # Sanitize command arguments
    sanitized_cmd = _sanitize_command_arguments(cmd)

    # Prepare subprocess execution parameters
    final_kwargs, check_flag = _prepare_subprocess_kwargs(kwargs)

    try:
        # Security: This subprocess.run call is safe because:
        # 1. Command structure validated above
        # 2. All components validated against allowlists
        # 3. Resource names sanitized to prevent injection
        # 4. Only 'docker' executable permitted
        # 5. Timeout enforced to prevent hanging
        return subprocess.run(sanitized_cmd, check=check_flag, **final_kwargs)  # type: ignore[return-value]
    except subprocess.CalledProcessError as e:
        logger.error(
            f"Command failed with exit code {e.returncode}: {' '.join(sanitized_cmd[:3])}...",
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


def _ensure_docker_available() -> int | None:
    """Check Docker availability and return error code if not available."""
    if not _check_docker_availability():
        logger.error("Docker is not available or not running. Please start Docker first.")
        return 1
    return None


def _get_service_name() -> str:
    """Get the appropriate service name based on the current mode."""
    return "tux"  # Both dev and prod use the same service name


def _get_resource_config(resource_type: str) -> dict[str, Any] | None:
    """Get resource configuration from RESOURCE_MAP."""
    return RESOURCE_MAP.get(resource_type)


def _get_tux_resources(resource_type: str) -> list[str]:
    """Get list of Tux-related Docker resources safely using data-driven approach."""
    cfg = _get_resource_config(resource_type)
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

    cfg = _get_resource_config(resource_type)
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
    if error_code := _ensure_docker_available():
        return error_code

    cmd = [*_get_compose_base_cmd(), "build"]
    if no_cache:
        cmd.append("--no-cache")
    if target:
        cmd.extend(["--target", target])

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
    if error_code := _ensure_docker_available():
        return error_code

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
@click.option("--quick", is_flag=True, help="Run quick validation tests only.")
@click.option("--comprehensive", is_flag=True, help="Run comprehensive test suite.")
def test(no_cache: bool, force_clean: bool, quick: bool, comprehensive: bool) -> int:
    """Run Docker performance and functionality tests.

    Uses the Python Docker toolkit for testing.
    """
    if error_code := _ensure_docker_available():
        return error_code

    # Use the Python Docker toolkit
    toolkit_script = Path.cwd() / "scripts" / "docker_toolkit.py"
    if not toolkit_script.exists():
        logger.error("Docker toolkit not found at scripts/docker_toolkit.py")
        return 1

    # Build command arguments
    cmd_args: list[str] = []

    if quick:
        cmd_args.append("quick")
    elif comprehensive:
        cmd_args.append("comprehensive")
    else:
        cmd_args.append("test")
        if no_cache:
            cmd_args.append("--no-cache")
        if force_clean:
            cmd_args.append("--force-clean")

    logger.info(f"Running Docker tests: {' '.join(cmd_args)}")

    # Execute the Python toolkit script
    try:
        cmd = ["python", str(toolkit_script), *cmd_args]
        result = _safe_subprocess_run(cmd, check=False)
    except Exception as e:
        logger.error(f"Failed to run Docker toolkit: {e}")
        return 1
    else:
        return result.returncode


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

    # Remove all dangling images using Docker's built-in filter
    try:
        result = _safe_subprocess_run(
            ["docker", "images", "--filter", "dangling=true", "--format", "{{.ID}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        dangling_image_ids = result.stdout.strip().split("\n") if result.stdout.strip() else []

        if dangling_image_ids:
            logger.info("Removing all dangling images using Docker's built-in filter")
            _safe_subprocess_run(
                ["docker", "rmi", "-f", *dangling_image_ids],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info(f"Removed {len(dangling_image_ids)} dangling images")

    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.warning(f"Failed to filter dangling images: {e}")

    # Filter out special networks
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
