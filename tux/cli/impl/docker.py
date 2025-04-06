"""Docker command implementations for Tux."""

from loguru import logger

from tux.cli.impl.core import run_command
from tux.utils.env import is_dev_mode


def _get_compose_base_cmd() -> list[str]:
    """Get the base docker compose command with appropriate -f flags."""
    base = ["docker", "compose", "-f", "docker-compose.yml"]
    if is_dev_mode():
        base.extend(["-f", "docker-compose.dev.yml"])
    return base


def docker_build() -> int:
    """Build the Docker images using Docker Compose V2."""
    cmd = [*_get_compose_base_cmd(), "build"]
    return run_command(cmd)


def docker_up(detach: bool = False, build: bool = False) -> int:
    """Start the services using Docker Compose V2.

    Parameters
    ----------
    detach : bool
        Run in detached mode.
    build : bool
        Build images before starting.
    """
    cmd = [*_get_compose_base_cmd(), "up"]
    if build:
        cmd.append("--build")
    if detach:
        cmd.append("-d")
    return run_command(cmd)


def docker_down() -> int:
    """Stop the services using Docker Compose V2."""
    cmd = [*_get_compose_base_cmd(), "down"]
    return run_command(cmd)


def docker_logs(follow: bool = False, service: str = "app") -> int:
    """Show logs for a service using Docker Compose V2.

    Parameters
    ----------
    follow : bool
        Follow log output.
    service : str
        The name of the service (defaults to 'app').
    """
    cmd = [*_get_compose_base_cmd(), "logs"]
    if follow:
        cmd.append("-f")
    cmd.append(service)
    return run_command(cmd)


def docker_ps() -> int:
    """List running containers managed by Docker Compose V2."""
    cmd = [*_get_compose_base_cmd(), "ps"]
    return run_command(cmd)


def docker_exec(service: str = "app", *exec_cmd: str) -> int:
    """Execute a command in a running container using Docker Compose V2.

    Parameters
    ----------
    service : str
        The service container to execute in (defaults to 'app').
    *exec_cmd : str
        The command and its arguments to execute.
    """
    if not exec_cmd:
        logger.error("Error: No command provided to execute.")
        return 1

    cmd = [*_get_compose_base_cmd(), "exec", service, *exec_cmd]
    return run_command(cmd)
