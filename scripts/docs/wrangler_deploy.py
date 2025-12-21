"""
Command: docs wrangler-deploy.

Deploys documentation to Cloudflare Workers.
"""

from pathlib import Path
from typing import Annotated

from typer import Option

from scripts.core import create_app
from scripts.docs.build import build
from scripts.proc import run_command
from scripts.ui import print_error, print_info, print_section, print_success

app = create_app()


@app.command(name="wrangler-deploy")
def wrangler_deploy(
    env: Annotated[
        str,
        Option("--env", "-e", help="Environment to deploy to"),
    ] = "production",
    dry_run: Annotated[
        bool,
        Option("--dry-run", help="Show deployment plan without deploying"),
    ] = False,
) -> None:
    """Deploy documentation to Cloudflare Workers."""
    print_section("Deploying to Cloudflare Workers", "blue")

    if not Path("wrangler.toml").exists():
        print_error("wrangler.toml not found. Please run from the project root.")
        return

    print_info("Building documentation...")

    build(strict=False)

    cmd = ["wrangler", "deploy", "--env", env]
    if dry_run:
        cmd.append("--dry-run")

    print_info(f"Deploying to {env} environment...")

    try:
        run_command(cmd, capture_output=False)
        print_success(f"Documentation deployed successfully to {env}")
    except Exception as e:
        print_error(f"Error: {e}")


if __name__ == "__main__":
    app()
