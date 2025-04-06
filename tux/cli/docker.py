"""Docker commands for the Tux CLI."""

import click

from tux.cli.core import command_registration_decorator, create_group

# Create the docker command group
docker_group = create_group("docker", "Docker management commands")


@command_registration_decorator(docker_group, name="build")
def build() -> int:
    """Build Docker images.

    Runs `docker compose build`.
    """
    from tux.cli.impl.docker import docker_build

    return docker_build()


@command_registration_decorator(docker_group, name="up")
@click.option("-d", "--detach", is_flag=True, help="Run containers in the background.")
@click.option("--build", is_flag=True, help="Build images before starting containers.")
def up(detach: bool, build: bool) -> int:
    """Start Docker services.

    Runs `docker compose up`.
    Can optionally build images first with --build.
    """
    from tux.cli.impl.docker import docker_up

    return docker_up(detach=detach, build=build)


@command_registration_decorator(docker_group, name="down")
def down() -> int:
    """Stop Docker services.

    Runs `docker compose down`.
    """
    from tux.cli.impl.docker import docker_down

    return docker_down()


@command_registration_decorator(docker_group, name="logs")
@click.option("-f", "--follow", is_flag=True, help="Follow log output.")
@click.argument("service", default="tux", required=False)
def logs(follow: bool, service: str) -> int:
    """Show logs for a Docker service.

    Runs `docker compose logs [service]`.
    """
    from tux.cli.impl.docker import docker_logs

    return docker_logs(follow=follow, service=service)


@command_registration_decorator(docker_group, name="ps")
def ps() -> int:
    """List running Docker containers.

    Runs `docker compose ps`.
    """
    from tux.cli.impl.docker import docker_ps

    return docker_ps()


@command_registration_decorator(docker_group, name="exec")
@click.argument("service", default="tux", required=False)
@click.argument("command", nargs=-1, required=True)
def exec_cmd(service: str, command: tuple[str, ...]) -> int:
    """Execute a command inside a running service container.

    Runs `docker compose exec [service] [command]`.
    """
    from tux.cli.impl.docker import docker_exec

    return docker_exec(service, *command)
