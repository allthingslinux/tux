"""
Command: docs wrangler-deploy.

Deploys documentation to Cloudflare Workers.
"""

from typing import Annotated

from typer import Exit, Option

from scripts.core import create_app
from scripts.docs.build import build
from scripts.docs.utils import has_wrangler_config
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

    if not has_wrangler_config():
        raise Exit(1)

    print_info("Building documentation...")

    try:
        # Build with strict=True to ensure we fail on any issue
        build(strict=True)
    except Exception as e:
        print_error(f"Build failed, aborting deployment: {e}")
        raise Exit(1) from e

    cmd = ["wrangler", "deploy", "--env", env]
    if dry_run:
        cmd.append("--dry-run")

    print_info(f"Deploying to {env} environment...")

    try:
        run_command(cmd, capture_output=False)
        print_success(f"Documentation deployed successfully to {env}")
    except Exception as e:
        print_error(f"Deployment failed: {e}")
        raise Exit(1) from e


if __name__ == "__main__":
    app()
