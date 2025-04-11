"""Docker commands for the Tux CLI."""

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


# Create the docker command group
docker_group = create_group("docker", "Docker management commands")


@command_registration_decorator(docker_group, name="build")
def build() -> int:
    """Build Docker images.

    Runs `docker compose build`.
    """
    cmd = [*_get_compose_base_cmd(), "build"]
    return run_command(cmd)


@command_registration_decorator(docker_group, name="up")
@click.option("-d", "--detach", is_flag=True, help="Run containers in the background.")
@click.option("--build", is_flag=True, help="Build images before starting containers.")
def up(detach: bool, build: bool) -> int:
    """Start Docker services.

    Runs `docker compose up`.
    Can optionally build images first with --build.
    """
    cmd = [*_get_compose_base_cmd(), "up"]
    if build:
        cmd.append("--build")
    if detach:
        cmd.append("-d")
    return run_command(cmd)


@command_registration_decorator(docker_group, name="down")
def down() -> int:
    """Stop Docker services.

    Runs `docker compose down`.
    """
    cmd = [*_get_compose_base_cmd(), "down"]
    return run_command(cmd)


@command_registration_decorator(docker_group, name="logs")
@click.option("-f", "--follow", is_flag=True, help="Follow log output.")
@click.argument("service", default="tux", required=False)
def logs(follow: bool, service: str) -> int:
    """Show logs for a Docker service.

    Runs `docker compose logs [service]`.
    """
    cmd = [*_get_compose_base_cmd(), "logs"]
    if follow:
        cmd.append("-f")
    cmd.append(service)
    return run_command(cmd)


@command_registration_decorator(docker_group, name="ps")
def ps() -> int:
    """List running Docker containers.

    Runs `docker compose ps`.
    """
    cmd = [*_get_compose_base_cmd(), "ps"]
    return run_command(cmd)


@command_registration_decorator(docker_group, name="exec")
@click.argument("service", default="tux", required=False)
@click.argument("command", nargs=-1, required=True)
def exec_cmd(service: str, command: tuple[str, ...]) -> int:
    """Execute a command inside a running service container.

    Runs `docker compose exec [service] [command]`.
    """
    if not command:
        logger.error("Error: No command provided to execute.")
        return 1

    cmd = [*_get_compose_base_cmd(), "exec", service, *command]
    return run_command(cmd)
