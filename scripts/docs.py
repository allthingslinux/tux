#!/usr/bin/env python3
"""
Documentation CLI Script

A unified interface for all documentation operations using the clean CLI infrastructure.
"""

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
    """Documentation CLI with unified interface for all documentation operations."""

    def __init__(self):
        super().__init__(
            name="docs",
            description="Documentation CLI - A unified interface for all documentation operations",
        )
        self._setup_command_registry()
        self._setup_commands()

    def _setup_command_registry(self) -> None:
        """Setup the command registry with all documentation commands."""
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
        ]

        for cmd in all_commands:
            self._command_registry.register_command(cmd)

    def _setup_commands(self) -> None:
        """Setup all documentation CLI commands using the command registry."""
        # Register all commands directly to the main app
        for command in self._command_registry.get_commands().values():
            self.add_command(
                command.func,
                name=command.name,
                help_text=command.help_text,
            )

    def _find_mkdocs_config(self) -> str | None:
        """Find the mkdocs.yml configuration file."""
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
        """Run a command and return success status."""
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

        cmd.extend(["-f", mkdocs_path])

        try:
            self._run_command(cmd)
            self.rich.print_success(f"Documentation server started at http://{host}:{port}")
        except subprocess.CalledProcessError:
            self.rich.print_error("Failed to start documentation server")

    def _run_mkdocs_command(self, command: str, *args: str, success_msg: str, error_msg: str) -> None:
        """Run a mkdocs command with common setup."""
        if not (mkdocs_path := self._find_mkdocs_config()):
            return

        cmd = ["uv", "run", "mkdocs", command, "-f", mkdocs_path, *args]

        try:
            self._run_command(cmd)
            self.rich.print_success(success_msg)
        except subprocess.CalledProcessError:
            self.rich.print_error(error_msg)

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

        args: list[str] = []
        if clean:
            args.append("--clean")
        if strict:
            args.append("--strict")
        if theme:
            args.extend(["--theme", theme])
        if site_dir:
            args.extend(["--site-dir", site_dir])
        if not use_directory_urls:
            args.append("--no-directory-urls")

        self._run_mkdocs_command(
            "build",
            *args,
            success_msg="Documentation built successfully",
            error_msg="Failed to build documentation",
        )

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

        args = [
            "-m",
            message,
            "--remote",
            remote,
            "--branch",
            branch,
        ]

        if force:
            args.append("--force")
        if no_history:
            args.append("--no-history")
        if ignore_version:
            args.append("--ignore-version")
        if clean:
            args.append("--clean")
        if strict:
            args.append("--strict")

        self._run_mkdocs_command(
            "gh-deploy",
            *args,
            success_msg="Documentation deployed successfully",
            error_msg="Failed to deploy documentation",
        )

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

        self._run_mkdocs_command(
            "build",
            "--strict",
            success_msg="Documentation validation passed",
            error_msg="Documentation validation failed",
        )

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


# Create the CLI app instance for mkdocs-typer
app = DocsCLI().app


def main() -> None:
    """Entry point for the Documentation CLI script."""
    cli = DocsCLI()
    cli.run()


if __name__ == "__main__":
    main()
