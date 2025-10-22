#!/usr/bin/env python3
"""
Documentation CLI Script.

A unified interface for all documentation operations using the clean CLI infrastructure.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Annotated

import yaml
from typer import Argument, Option  # type: ignore[attr-defined]

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from scripts.base import BaseCLI
from scripts.registry import Command


class DocsCLI(BaseCLI):
    """Documentation CLI with unified interface for all documentation operations.

    Provides a comprehensive set of commands for managing MkDocs documentation,
    including serving, building, deploying, and maintenance operations.
    """

    def __init__(self):
        """Initialize the DocsCLI application.

        Sets up the CLI with documentation-specific commands and configures
        the command registry for MkDocs operations.
        """
        super().__init__(
            name="docs",
            description="Documentation CLI - A unified interface for all documentation operations",
        )
        self._setup_command_registry()
        self._setup_commands()

    def _setup_command_registry(self) -> None:
        """Set up the command registry with all documentation commands."""
        # All commands directly registered without groups
        all_commands = [
            # Core MkDocs commands
            Command("serve", self.serve, "Serve documentation locally with live reload"),
            Command("build", self.build, "Build documentation site for production"),
            Command("deploy", self.deploy, "Deploy documentation to GitHub Pages"),
            Command("gh-deploy", self.gh_deploy, "Deploy to GitHub Pages (alias for deploy)"),
            Command("new", self.new_project, "Create a new MkDocs project"),
            Command("get-deps", self.get_deps, "Show required PyPI packages from plugins"),
            # Documentation management
            Command("clean", self.clean, "Clean documentation build artifacts"),
            Command("validate", self.validate, "Validate documentation structure and links"),
            Command("check", self.check, "Check documentation for issues"),
            # Development tools
            Command("new-page", self.new_page, "Create a new documentation page"),
            Command("watch", self.watch, "Watch for changes and rebuild automatically"),
            Command("lint", self.lint, "Lint documentation files"),
            # Information
            Command("info", self.info, "Show documentation configuration and status"),
            Command("list", self.list_pages, "List all documentation pages"),
            # Cloudflare Workers deployment commands
            Command("wrangler-dev", self.wrangler_dev, "Start local Wrangler development server"),
            Command("wrangler-deploy", self.wrangler_deploy, "Deploy documentation to Cloudflare Workers"),
            Command("wrangler-deployments", self.wrangler_deployments, "List deployment history"),
            Command("wrangler-versions", self.wrangler_versions, "List and manage versions"),
            Command("wrangler-tail", self.wrangler_tail, "View real-time logs from deployed docs"),
            Command("wrangler-rollback", self.wrangler_rollback, "Rollback to a previous deployment"),
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

    def _find_mkdocs_config(self) -> str | None:
        """Find the mkdocs.yml configuration file.

        Returns
        -------
        str | None
            Path to mkdocs.yml if found, None otherwise.
        """
        current_dir = Path.cwd()

        # Check if we're in the docs directory
        if (current_dir / "mkdocs.yml").exists():
            return "mkdocs.yml"

        # Check if we're in the root repo with docs subdirectory
        if (current_dir / "docs" / "mkdocs.yml").exists():
            return "docs/mkdocs.yml"

        self.rich.print_error("Can't find mkdocs.yml file. Please run from the project root or docs directory.")
        return None

    def _run_command(self, command: list[str]) -> None:
        """Run a command and return success status.

        Raises
        ------
        FileNotFoundError
            If the command is not found.
        CalledProcessError
            If the command fails.
        """
        try:
            self.rich.print_info(f"Running: {' '.join(command)}")
            subprocess.run(command, check=True)
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
        host: Annotated[str, Option("--host", "-h", help="Host to serve on")] = "127.0.0.1",
        port: Annotated[int, Option("--port", "-p", help="Port to serve on")] = 8000,
        dirty: Annotated[bool, Option("--dirty", help="Only re-build files that have changed")] = False,
        no_livereload: Annotated[bool, Option("--no-livereload", help="Disable live reloading")] = False,
        clean: Annotated[bool, Option("--clean", help="Build without effects of mkdocs serve")] = False,
        strict: Annotated[bool, Option("--strict", help="Enable strict mode")] = False,
        watch_theme: Annotated[bool, Option("--watch-theme", help="Watch theme files for changes")] = False,
    ) -> None:
        """Serve documentation locally with live reload."""
        self.rich.print_section("📚 Serving Documentation", "blue")

        if not (mkdocs_path := self._find_mkdocs_config()):
            return

        cmd = ["uv", "run", "mkdocs", "serve", f"--dev-addr={host}:{port}"]

        if dirty:
            cmd.append("--dirty")
        if no_livereload:
            cmd.append("--no-livereload")
        if clean:
            cmd.append("--clean")
        if strict:
            cmd.append("--strict")
        if watch_theme:
            cmd.append("--watch-theme")

        cmd.extend(["-f", mkdocs_path])

        try:
            self._run_command(cmd)
            self.rich.print_success(f"Documentation server started at http://{host}:{port}")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to start documentation server")

    def build(
        self,
        clean: Annotated[bool, Option("--clean", help="Remove old files from site_dir before building")] = True,
        strict: Annotated[bool, Option("--strict", help="Enable strict mode")] = False,
        theme: Annotated[str, Option("--theme", "-t", help="Theme to use (mkdocs or readthedocs)")] = "",
        site_dir: Annotated[str, Option("--site-dir", "-d", help="Directory to output the build result")] = "",
        use_directory_urls: Annotated[
            bool,
            Option("--use-directory-urls", help="Use directory URLs when building pages"),
        ] = True,
    ) -> None:
        """Build documentation site for production."""
        self.rich.print_section("🏗️ Building Documentation", "blue")

        if not (mkdocs_path := self._find_mkdocs_config()):
            return

        cmd = ["uv", "run", "mkdocs", "build", "-f", mkdocs_path]

        if clean:
            cmd.append("--clean")
        if strict:
            cmd.append("--strict")
        if theme:
            cmd.extend(["--theme", theme])
        if site_dir:
            cmd.extend(["--site-dir", site_dir])
        if not use_directory_urls:
            cmd.append("--no-directory-urls")

        try:
            self._run_command(cmd)
            self.rich.print_success("Documentation built successfully")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to build documentation")

    def deploy(
        self,
        message: Annotated[str, Option("--message", "-m", help="Commit message")] = "Deploy documentation",
        remote: Annotated[str, Option("--remote", help="Remote repository")] = "origin",
        branch: Annotated[str, Option("--branch", help="Branch to deploy to")] = "gh-pages",
        force: Annotated[bool, Option("--force", help="Force the push to the repository")] = False,
        no_history: Annotated[
            bool,
            Option("--no-history", help="Replace the whole Git history with one new commit"),
        ] = False,
        ignore_version: Annotated[
            bool,
            Option(
                "--ignore-version",
                help="Ignore check that build is not being deployed with an older version of MkDocs",
            ),
        ] = False,
        clean: Annotated[bool, Option("--clean", help="Remove old files from site_dir before building")] = True,
        strict: Annotated[bool, Option("--strict", help="Enable strict mode")] = False,
    ) -> None:
        """Deploy documentation to GitHub Pages."""
        self.rich.print_section("🚀 Deploying Documentation", "blue")

        if not (mkdocs_path := self._find_mkdocs_config()):
            return

        cmd = [
            "uv",
            "run",
            "mkdocs",
            "gh-deploy",
            "-f",
            mkdocs_path,
            "-m",
            message,
            "--remote",
            remote,
            "--branch",
            branch,
        ]

        if force:
            cmd.append("--force")
        if no_history:
            cmd.append("--no-history")
        if ignore_version:
            cmd.append("--ignore-version")
        if clean:
            cmd.append("--clean")
        if strict:
            cmd.append("--strict")

        try:
            self._run_command(cmd)
            self.rich.print_success("Documentation deployed successfully")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to deploy documentation")

    def gh_deploy(
        self,
        message: Annotated[str, Option("--message", "-m", help="Commit message")] = "Deploy documentation",
    ) -> None:
        """Deploy to GitHub Pages (alias for deploy)."""
        self.deploy(message=message)

    def clean(self) -> None:
        """Clean documentation build artifacts."""
        self.rich.print_section("🧹 Cleaning Documentation", "blue")

        # Clean build directory
        build_dir = Path("build/docs")
        self._clean_directory(build_dir, "Build directory")

        # Clean MkDocs cache
        cache_dir = Path("docs/.cache")
        self._clean_directory(cache_dir, "MkDocs cache")

    def validate(self) -> None:
        """Validate documentation structure and links."""
        self.rich.print_section("✅ Validating Documentation", "blue")

        if not (mkdocs_path := self._find_mkdocs_config()):
            return

        cmd = ["uv", "run", "mkdocs", "build", "--strict", "-f", mkdocs_path]

        try:
            self._run_command(cmd)
            self.rich.print_success("Documentation validation passed")
        except subprocess.CalledProcessError:
            self.rich.print_error("Documentation validation failed")

    def check(self) -> None:
        """Check documentation for issues."""
        self.rich.print_section("🔍 Checking Documentation", "blue")

        if not (mkdocs_path := self._find_mkdocs_config()):
            return

        # Check for common issues
        issues: list[str] = []

        # Check if mkdocs.yml exists and is valid
        try:
            with Path(mkdocs_path).open() as f:
                yaml.safe_load(f)
            self.rich.print_success("mkdocs.yml is valid")
        except Exception as e:
            issues.append(f"Invalid mkdocs.yml: {e}")

        # Check if docs directory exists
        docs_dir = Path("docs/content")
        if not docs_dir.exists():
            issues.append("docs/content directory not found")

        # Check for index.md
        index_file = docs_dir / "index.md"
        if not index_file.exists():
            issues.append("index.md not found in docs/content")

        if issues:
            self.rich.print_error("Documentation issues found:")
            for issue in issues:
                self.rich.print_error(f"  • {issue}")
        else:
            self.rich.print_success("No documentation issues found")

    def new_project(
        self,
        project_dir: Annotated[str, Argument(help="Project directory name")],
    ) -> None:
        """Create a new MkDocs project."""
        self.rich.print_section("🆕 Creating New MkDocs Project", "blue")

        cmd = ["uv", "run", "mkdocs", "new", project_dir]

        try:
            self._run_command(cmd)
            self.rich.print_success(f"New MkDocs project created in '{project_dir}'")
            self.rich.print_info(f"To get started, run: cd {project_dir} && uv run mkdocs serve")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to create new MkDocs project")

    def get_deps(self) -> None:
        """Show required PyPI packages inferred from plugins in mkdocs.yml."""
        self.rich.print_section("📦 MkDocs Dependencies", "blue")

        if not (mkdocs_path := self._find_mkdocs_config()):
            return

        cmd = ["uv", "run", "mkdocs", "get-deps", "-f", mkdocs_path]

        try:
            self._run_command(cmd)
            self.rich.print_success("Dependencies retrieved successfully")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to get dependencies")

    def new_page(
        self,
        title: Annotated[str, Argument(help="Page title")],
        path: Annotated[str, Option("--path", "-p", help="Page path (e.g., dev/new-feature)")] = "",
    ) -> None:
        """Create a new documentation page."""
        self.rich.print_section("📄 Creating New Page", "blue")

        docs_dir = Path("docs/content")
        if not docs_dir.exists():
            self.rich.print_error("docs/content directory not found")
            return

        # Generate path from title if not provided
        if not path:
            path = title.lower().replace(" ", "-").replace("_", "-")

        # Ensure path ends with .md
        if not path.endswith(".md"):
            path += ".md"

        page_path = docs_dir / path

        # Create directory if needed
        page_path.parent.mkdir(parents=True, exist_ok=True)

        # Create the page content
        content = f"""# {title}

<!-- Add your content here -->

## Overview

<!-- Describe what this page covers -->

## Details

<!-- Add detailed information -->

## Examples

<!-- Add code examples or usage instructions -->

## Related

<!-- Link to related pages -->
"""

        try:
            page_path.write_text(content)
            self.rich.print_success(f"Created new page: {page_path}")
        except Exception as e:
            self.rich.print_error(f"Failed to create page: {e}")

    def watch(self) -> None:
        """Watch for changes and rebuild automatically."""
        self.rich.print_section("👀 Watching Documentation", "blue")
        self.rich.print_info("Starting documentation server with auto-reload...")
        self.serve()

    def lint(self) -> None:
        """Lint documentation files."""
        self.rich.print_section("🔍 Linting Documentation", "blue")

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

    def info(self) -> None:
        """Show documentation configuration and status."""
        self.rich.print_section("📋 Documentation Information", "blue")

        # Show mkdocs.yml location
        if mkdocs_path := self._find_mkdocs_config():
            self.rich.print_success(f"MkDocs config: {mkdocs_path}")
        else:
            return

        # Show docs directory structure
        docs_dir = Path("docs/content")
        if docs_dir.exists():
            self.rich.print_info(f"Content directory: {docs_dir}")

            # Count files
            md_files = list(docs_dir.rglob("*.md"))
            self.rich.print_info(f"Markdown files: {len(md_files)}")

            # Show build directory
            build_dir = Path("build/docs")
            if build_dir.exists():
                self.rich.print_info(f"Build directory: {build_dir} (exists)")
            else:
                self.rich.print_info(f"Build directory: {build_dir} (not built)")
        else:
            self.rich.print_warning("Content directory not found")

    def list_pages(self) -> None:
        """List all documentation pages."""
        self.rich.print_section("📚 Documentation Pages", "blue")

        docs_dir = Path("docs/content")
        if not docs_dir.exists():
            self.rich.print_error("docs/content directory not found")
            return

        md_files = list(docs_dir.rglob("*.md"))
        if not md_files:
            self.rich.print_warning("No markdown files found")
            return

        # Create a table of pages
        table_data: list[tuple[str, str]] = []
        for md_file in sorted(md_files):
            rel_path = md_file.relative_to(docs_dir)
            try:
                first_line = md_file.read_text().split("\n")[0].strip()
                title = first_line.lstrip("# ") if first_line.startswith("#") else "No title"
            except Exception:
                title = "Error reading file"

            table_data.append((str(rel_path), title))

        if table_data:
            self.rich.print_rich_table("Documentation Pages", [("Path", "cyan"), ("Title", "green")], table_data)
        else:
            self.rich.print_info("No pages found")

    def wrangler_dev(
        self,
        port: Annotated[int, Option("--port", "-p", help="Port to serve on")] = 8787,
        remote: Annotated[bool, Option("--remote", help="Run on remote cloudflare infrastructure")] = False,
    ) -> None:  # sourcery skip: class-extract-method
        """Start local Wrangler development server with static assets.

        This runs the docs using Cloudflare Workers locally, useful for testing
        the production environment before deployment.
        """
        self.rich.print_section("🔧 Starting Wrangler Dev Server", "blue")

        docs_dir = Path("docs")
        if not docs_dir.exists():
            self.rich.print_error("docs directory not found")
            return

        # Build docs first
        self.rich.print_info("Building documentation...")
        self.build(strict=True)

        # Start wrangler dev
        cmd = ["wrangler", "dev", f"--port={port}"]
        if remote:
            cmd.append("--remote")

        self.rich.print_info(f"Starting Wrangler dev server on port {port}...")

        original_dir = Path.cwd()
        try:
            # Change to docs directory
            docs_path = Path("docs")
            if docs_path.exists():
                os.chdir(docs_path)

            self._run_command(cmd)
            self.rich.print_success(f"Wrangler dev server started at http://localhost:{port}")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to start Wrangler dev server")
        except Exception as e:
            self.rich.print_error(f"Error: {e}")
        finally:
            os.chdir(original_dir)

    def wrangler_deploy(
        self,
        env: Annotated[str, Option("--env", "-e", help="Environment to deploy to")] = "production",
        dry_run: Annotated[bool, Option("--dry-run", help="Show what would be deployed")] = False,
    ) -> None:
        """Deploy documentation to Cloudflare Workers.

        Builds the docs and deploys to Cloudflare using the wrangler.toml configuration.
        Use --env to deploy to preview or production environments.
        """
        self.rich.print_section("🚀 Deploying to Cloudflare Workers", "blue")

        # Build docs first (without strict to allow warnings)
        self.rich.print_info("Building documentation...")
        self.build(strict=False)

        # Deploy with wrangler - always specify env to avoid warning
        cmd = ["wrangler", "deploy", "--env", env]
        if dry_run:
            cmd.append("--dry-run")

        self.rich.print_info(f"Deploying to {env} environment...")

        original_dir = Path.cwd()
        try:
            # Change to docs directory
            docs_path = Path("docs")
            if docs_path.exists():
                os.chdir(docs_path)

            self._run_command(cmd)
            self.rich.print_success(f"Documentation deployed successfully to {env}")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to deploy documentation")
        except Exception as e:
            self.rich.print_error(f"Error: {e}")
        finally:
            os.chdir(original_dir)

    def wrangler_deployments(
        self,
        limit: Annotated[int, Option("--limit", "-l", help="Number of deployments to show")] = 10,
    ) -> None:
        """List deployment history for the documentation site.

        Shows recent deployments with their status, version, and timestamp.
        """
        self.rich.print_section("📜 Deployment History", "blue")

        cmd = ["wrangler", "deployments", "list"]
        if limit:
            cmd.extend(["--limit", str(limit)])

        original_dir = Path.cwd()
        try:
            docs_path = Path("docs")
            if docs_path.exists():
                os.chdir(docs_path)

            self._run_command(cmd)
            self.rich.print_success("Deployment history retrieved")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to get deployment history")
        except Exception as e:
            self.rich.print_error(f"Error: {e}")
        finally:
            os.chdir(original_dir)

    def wrangler_versions(
        self,
        action: Annotated[
            str,
            Option("--action", "-a", help="Action: list, view, or upload"),
        ] = "list",
        version_id: Annotated[str, Option("--version-id", help="Version ID for view action")] = "",
        alias: Annotated[str, Option("--alias", help="Preview alias name for upload")] = "",
    ) -> None:
        """List and manage versions of the documentation.

        Actions:
        - list: Show all versions
        - view: Show details of a specific version
        - upload: Create a new version with optional preview alias
        """
        self.rich.print_section("🫧 Managing Versions", "blue")

        cmd = ["wrangler", "versions", action]

        if action == "view" and version_id:
            cmd.append(version_id)
        elif action == "upload" and alias:
            cmd.extend(["--preview-alias", alias])

        original_dir = Path.cwd()
        try:
            docs_path = Path("docs")
            if docs_path.exists():
                os.chdir(docs_path)

            self._run_command(cmd)
            self.rich.print_success(f"Version {action} completed")
        except subprocess.CalledProcessError:
            self.rich.print_error(f"Failed to {action} versions")
        except Exception as e:
            self.rich.print_error(f"Error: {e}")
        finally:
            os.chdir(original_dir)

    def wrangler_tail(
        self,
        format_output: Annotated[str, Option("--format", help="Output format: json or pretty")] = "pretty",
        status: Annotated[str, Option("--status", help="Filter by status: ok, error, or canceled")] = "",
    ) -> None:
        """View real-time logs from deployed documentation.

        Tails the logs of your deployed Workers documentation, showing requests and errors.
        """
        self.rich.print_section("🦚 Tailing Logs", "blue")

        cmd = ["wrangler", "tail"]
        if format_output:
            cmd.extend(["--format", format_output])
        if status:
            cmd.extend(["--status", status])

        self.rich.print_info("Starting log tail... (Ctrl+C to stop)")

        original_dir = Path.cwd()
        try:
            docs_path = Path("docs")
            if docs_path.exists():
                os.chdir(docs_path)

            self._run_command(cmd)
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to tail logs")
        except KeyboardInterrupt:
            self.rich.print_info("\nLog tail stopped")
        except Exception as e:
            self.rich.print_error(f"Error: {e}")
        finally:
            os.chdir(original_dir)

    def wrangler_rollback(
        self,
        version_id: Annotated[str, Option("--version-id", help="Version ID to rollback to")] = "",
        message: Annotated[str, Option("--message", "-m", help="Rollback message")] = "",
    ) -> None:
        """Rollback to a previous deployment.

        Use wrangler-deployments to find the version ID you want to rollback to.
        """
        self.rich.print_section("🔙 Rolling Back Deployment", "blue")

        if not version_id:
            self.rich.print_error("Version ID is required. Use wrangler-deployments to find version IDs.")
            return

        cmd = ["wrangler", "rollback", version_id]
        if message:
            cmd.extend(["--message", message])

        self.rich.print_warning(f"Rolling back to version: {version_id}")

        original_dir = Path.cwd()
        try:
            docs_path = Path("docs")
            if docs_path.exists():
                os.chdir(docs_path)

            self._run_command(cmd)
            self.rich.print_success(f"Successfully rolled back to version {version_id}")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to rollback")
        except Exception as e:
            self.rich.print_error(f"Error: {e}")
        finally:
            os.chdir(original_dir)


# Create the CLI app instance for mkdocs-typer
app = DocsCLI().app


def main() -> None:
    """Entry point for the Documentation CLI script."""
    cli = DocsCLI()
    cli.run()


if __name__ == "__main__":
    main()
