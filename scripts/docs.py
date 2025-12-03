#!/usr/bin/env python3
"""
Documentation CLI Script.

Documentation operations management.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated

from typer import Option  # type: ignore[attr-defined]

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from scripts.base import BaseCLI
from scripts.registry import Command


class DocsCLI(BaseCLI):
    """Documentation operations management.

    Commands for managing Zensical documentation, including serving,
    building, deploying, and maintenance operations.
    """

    def __init__(self):
        """Initialize the DocsCLI application.

        Sets up the CLI with documentation-specific commands and configures
        the command registry for Zensical operations.
        """
        super().__init__(
            name="docs",
            description="Documentation operations",
        )
        self._setup_command_registry()
        self._setup_commands()

    def _setup_command_registry(self) -> None:
        """Set up the command registry with all documentation commands."""
        # All commands directly registered without groups
        all_commands = [
            # Core Zensical commands
            Command(
                "serve",
                self.serve,
                "Serve documentation locally",
            ),
            Command("build", self.build, "Build documentation site"),
            Command("lint", self.lint, "Lint documentation files"),
            # Cloudflare Workers deployment commands
            Command(
                "wrangler-dev",
                self.wrangler_dev,
                "Start local Wrangler development server",
            ),
            Command(
                "wrangler-deploy",
                self.wrangler_deploy,
                "Deploy documentation to Cloudflare Workers",
            ),
            Command(
                "wrangler-deployments",
                self.wrangler_deployments,
                "List deployment history",
            ),
            Command(
                "wrangler-versions",
                self.wrangler_versions,
                "List and manage versions",
            ),
            Command(
                "wrangler-tail",
                self.wrangler_tail,
                "View real-time logs from deployed docs",
            ),
            Command(
                "wrangler-rollback",
                self.wrangler_rollback,
                "Rollback to a previous deployment",
            ),
        ]

        for cmd in all_commands:
            self._command_registry.register_command(cmd)

    def _setup_commands(self) -> None:
        """Set up all documentation CLI commands using the command registry."""
        # Register all commands directly to the main app
        for command in self._command_registry.get_commands().values():
            self.add_command(
                command.func,
                name=command.name,
                help_text=command.help_text,
            )

    def _find_zensical_config(self) -> str | None:
        """Find the zensical.toml configuration file.

        Returns
        -------
        str | None
            Path to zensical.toml if found, None otherwise.
        """
        current_dir = Path.cwd()

        # Check if we're in the root repo
        if (current_dir / "zensical.toml").exists():
            return "zensical.toml"

        self.rich.print_error(
            "Can't find zensical.toml file. Please run from the project root.",
        )
        return None

    def _run_command(self, command: list[str]) -> None:
        """Run a command and return success status.

        Overrides base implementation to print command info before execution.
        Environment variables are handled by the base class.

        Raises
        ------
        FileNotFoundError
            If the command is not found.
        CalledProcessError
            If the command fails.
        """
        try:
            self.rich.print_info(f"Running: {' '.join(command)}")
            # Call parent implementation which handles env vars
            super()._run_command(command)
        except subprocess.CalledProcessError as e:
            self.rich.print_error(f"Command failed with exit code {e.returncode}")
            raise
        except FileNotFoundError:
            self.rich.print_error(f"Command not found: {command[0]}")
            raise

    def _clean_directory(self, path: Path, name: str) -> None:
        """Clean a directory if it exists."""
        if path.exists():
            shutil.rmtree(path)
            self.rich.print_success(f"{name} cleaned")
        else:
            self.rich.print_info(f"No {name} found")

    def serve(
        self,
        dev_addr: Annotated[
            str,
            Option(
                "--dev-addr",
                "-a",
                help="IP address and port (default: localhost:8000)",
            ),
        ] = "localhost:8000",
        open_browser: Annotated[
            bool,
            Option("--open", "-o", help="Open preview in default browser"),
        ] = False,
        strict: Annotated[
            bool,
            Option("--strict", "-s", help="Strict mode (currently unsupported)"),
        ] = False,
    ) -> None:
        """Serve documentation locally with live reload."""
        self.rich.print_section("Serving Documentation", "blue")

        if not self._find_zensical_config():
            return

        cmd = [
            "uv",
            "run",
            "zensical",
            "serve",
            "--dev-addr",
            dev_addr,
        ]

        if open_browser:
            cmd.append("--open")

        if strict:
            cmd.append("--strict")

        try:
            # Run server command without capturing output (for real-time streaming)
            # This allows zensical serve to run interactively and stream output
            # Note: --open flag will automatically open browser if provided
            self.rich.print_info(
                f"Starting documentation server at {dev_addr}",
            )
            subprocess.run(cmd, check=True, env=os.environ.copy())
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to start documentation server")
        except KeyboardInterrupt:
            self.rich.print_info("\nDocumentation server stopped")

    def build(
        self,
        clean: Annotated[
            bool,
            Option("--clean", "-c", help="Clean cache"),
        ] = False,
        strict: Annotated[
            bool,
            Option("--strict", "-s", help="Strict mode (currently unsupported)"),
        ] = False,
    ) -> None:
        """Build documentation site for production."""
        self.rich.print_section("Building Documentation", "blue")

        if not self._find_zensical_config():
            return

        cmd = ["uv", "run", "zensical", "build"]

        if clean:
            cmd.append("--clean")
        if strict:
            cmd.append("--strict")

        try:
            # Run build command without capturing output (for real-time streaming)
            # This allows zensical build to stream output to the terminal
            self.rich.print_info("Building documentation...")
            subprocess.run(cmd, check=True, env=os.environ.copy())
            self.rich.print_success("Documentation built successfully")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to build documentation")
        except KeyboardInterrupt:
            self.rich.print_info("\nBuild interrupted")

    def lint(self) -> None:
        """Lint documentation files."""
        self.rich.print_section("Linting Documentation", "blue")

        # Check for common markdown issues
        docs_dir = Path("docs/content")
        if not docs_dir.exists():
            self.rich.print_error("docs/content directory not found")
            return

        issues: list[str] = []
        for md_file in docs_dir.rglob("*.md"):
            try:
                content = md_file.read_text()

                # Check for common issues
                if content.strip() == "":
                    issues.append(f"Empty file: {md_file}")
                elif not content.startswith("#"):
                    issues.append(f"Missing title: {md_file}")
                elif "TODO" in content or "FIXME" in content:
                    issues.append(f"Contains TODO/FIXME: {md_file}")

            except Exception as e:
                issues.append(f"Error reading {md_file}: {e}")

        if issues:
            self.rich.print_warning("Documentation linting issues found:")
            for issue in issues:
                self.rich.print_warning(f"  • {issue}")
        else:
            self.rich.print_success("No documentation linting issues found")

    def wrangler_dev(
        self,
        port: Annotated[int, Option("--port", "-p", help="Port to serve on")] = 8787,
        remote: Annotated[
            bool,
            Option("--remote", help="Run on remote Cloudflare infrastructure"),
        ] = False,
    ) -> None:  # sourcery skip: class-extract-method
        """Start local Wrangler development server.

        This runs the docs using Cloudflare Workers locally, useful for testing
        the production environment before deployment.
        """
        self.rich.print_section("Starting Wrangler Dev Server", "blue")

        if not Path("wrangler.toml").exists():
            self.rich.print_error(
                "wrangler.toml not found. Please run from the project root.",
            )
            return

        # Build docs first
        self.rich.print_info("Building documentation...")
        self.build(strict=True)

        # Start wrangler dev
        cmd = ["wrangler", "dev", f"--port={port}"]
        if remote:
            cmd.append("--remote")

        self.rich.print_info(f"Starting Wrangler dev server on port {port}...")

        try:
            self._run_command(cmd)
            self.rich.print_success(
                f"Wrangler dev server started at http://localhost:{port}",
            )
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to start Wrangler dev server")
        except Exception as e:
            self.rich.print_error(f"Error: {e}")

    def wrangler_deploy(
        self,
        env: Annotated[
            str,
            Option("--env", "-e", help="Environment to deploy to"),
        ] = "production",
        dry_run: Annotated[
            bool,
            Option("--dry-run", help="Show deployment plan without deploying"),
        ] = False,
    ) -> None:
        """Deploy documentation to Cloudflare Workers.

        Builds the docs and deploys to Cloudflare using the wrangler.toml configuration.
        Cloudflare Workers will automatically run tests and include coverage reports.
        Use --env to deploy to preview or production environments.
        """
        self.rich.print_section("Deploying to Cloudflare Workers", "blue")

        if not Path("wrangler.toml").exists():
            self.rich.print_error(
                "wrangler.toml not found. Please run from the project root.",
            )
            return

        # Build docs first (without strict to allow warnings)
        self.rich.print_info("Building documentation...")
        self.build(strict=False)

        # Deploy with wrangler - always specify env to avoid warning
        cmd = ["wrangler", "deploy", "--env", env]
        if dry_run:
            cmd.append("--dry-run")

        self.rich.print_info(f"Deploying to {env} environment...")

        try:
            self._run_command(cmd)
            self.rich.print_success(f"Documentation deployed successfully to {env}")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to deploy documentation")
        except Exception as e:
            self.rich.print_error(f"Error: {e}")

    def wrangler_deployments(
        self,
        limit: Annotated[
            int,
            Option("--limit", "-l", help="Maximum number of deployments to show"),
        ] = 10,
    ) -> None:
        """List deployment history for the documentation site.

        Shows recent deployments with their status, version, and timestamp.
        """
        self.rich.print_section("Deployment History", "blue")

        if not Path("wrangler.toml").exists():
            self.rich.print_error(
                "wrangler.toml not found. Please run from the project root.",
            )
            return

        cmd = ["wrangler", "deployments", "list"]
        if limit:
            cmd.extend(["--limit", str(limit)])

        try:
            self._run_command(cmd)
            self.rich.print_success("Deployment history retrieved")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to get deployment history")
        except Exception as e:
            self.rich.print_error(f"Error: {e}")

    def wrangler_versions(
        self,
        action: Annotated[
            str,
            Option("--action", "-a", help="Action to perform: list, view, or upload"),
        ] = "list",
        version_id: Annotated[
            str,
            Option("--version-id", help="Version ID to view"),
        ] = "",
        alias: Annotated[
            str,
            Option("--alias", help="Preview alias name"),
        ] = "",
    ) -> None:
        """List and manage versions of the documentation.

        Actions:
        - list: Show all versions
        - view: Show details of a specific version
        - upload: Create a new version with optional preview alias
        """
        self.rich.print_section("Managing Versions", "blue")

        if not Path("wrangler.toml").exists():
            self.rich.print_error(
                "wrangler.toml not found. Please run from the project root.",
            )
            return

        cmd = ["wrangler", "versions", action]

        if action == "view" and version_id:
            cmd.append(version_id)
        elif action == "upload" and alias:
            cmd.extend(["--preview-alias", alias])

        try:
            self._run_command(cmd)
            self.rich.print_success(f"Version {action} completed")
        except subprocess.CalledProcessError:
            self.rich.print_error(f"Failed to {action} versions")
        except Exception as e:
            self.rich.print_error(f"Error: {e}")

    def wrangler_tail(
        self,
        format_output: Annotated[
            str,
            Option("--format", help="Output format: json or pretty"),
        ] = "pretty",
        status: Annotated[
            str,
            Option("--status", help="Filter by status: ok, error, or canceled"),
        ] = "",
    ) -> None:
        """View real-time logs from deployed documentation.

        Tails the logs of your deployed Workers documentation, showing requests and errors.
        """
        self.rich.print_section("Tailing Logs", "blue")

        if not Path("wrangler.toml").exists():
            self.rich.print_error(
                "wrangler.toml not found. Please run from the project root.",
            )
            return

        cmd = ["wrangler", "tail"]
        if format_output:
            cmd.extend(["--format", format_output])
        if status:
            cmd.extend(["--status", status])

        self.rich.print_info("Starting log tail... (Ctrl+C to stop)")

        try:
            self._run_command(cmd)
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to tail logs")
        except KeyboardInterrupt:
            self.rich.print_info("\nLog tail stopped")
        except Exception as e:
            self.rich.print_error(f"Error: {e}")

    def wrangler_rollback(
        self,
        version_id: Annotated[
            str,
            Option("--version-id", help="Version ID to rollback to"),
        ] = "",
        message: Annotated[
            str,
            Option("--message", "-m", help="Rollback message"),
        ] = "",
    ) -> None:
        """Rollback to a previous deployment.

        Use wrangler-deployments to find the version ID you want to rollback to.
        """
        self.rich.print_section("Rolling Back Deployment", "blue")

        if not Path("wrangler.toml").exists():
            self.rich.print_error(
                "wrangler.toml not found. Please run from the project root.",
            )
            return

        if not version_id:
            self.rich.print_error(
                "Version ID is required. Use wrangler-deployments to find version IDs.",
            )
            return

        cmd = ["wrangler", "rollback", version_id]
        if message:
            cmd.extend(["--message", message])

        self.rich.print_warning(f"Rolling back to version: {version_id}")

        try:
            self._run_command(cmd)
            self.rich.print_success(f"Successfully rolled back to version {version_id}")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to rollback")
        except Exception as e:
            self.rich.print_error(f"Error: {e}")


# Create the CLI app instance
app = DocsCLI().app


def main() -> None:
    """Entry point for the Documentation CLI script."""
    cli = DocsCLI()
    cli.run()


if __name__ == "__main__":
    main()
