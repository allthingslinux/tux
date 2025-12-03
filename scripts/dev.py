#!/usr/bin/env python3
"""
Development CLI Script.

Development tools and workflows.
"""

import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from typer import Option  # type: ignore[attr-defined]

# Add current directory to path for scripts imports
scripts_path = Path(__file__).parent
sys.path.insert(0, str(scripts_path))

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from scripts.base import BaseCLI
from scripts.registry import Command


class DevCLI(BaseCLI):
    """Development tools and workflows.

    Commands for code quality checks, formatting, type checking,
    documentation linting, and workflow automation.
    """

    def __init__(self):
        """Initialize the DevCLI application.

        Sets up the CLI with development-specific commands and configures
        the command registry for development operations.
        """
        super().__init__(
            name="dev",
            description="Development tools",
        )
        self._setup_command_registry()
        self._setup_commands()

    def _setup_command_registry(self) -> None:
        """Set up the command registry with all development commands."""
        # All commands directly registered without groups
        all_commands = [
            # Code quality commands
            Command("lint", self.lint, "Run linting checks"),
            Command("lint-fix", self.lint_fix, "Run linting and apply fixes"),
            Command("format", self.format_code, "Format code"),
            Command("type-check", self.type_check, "Check types"),
            Command(
                "lint-docstring",
                self.lint_docstring,
                "Lint docstrings",
            ),
            Command(
                "docstring-coverage",
                self.docstring_coverage,
                "Check docstring coverage",
            ),
            Command("pre-commit", self.pre_commit, "Run pre-commit checks"),
            Command("clean", self.clean, "Clean temporary files and cache"),
            Command("all", self.run_all_checks, "Run all development checks"),
        ]

        for cmd in all_commands:
            self._command_registry.register_command(cmd)

    def _setup_commands(self) -> None:
        """Set up all development CLI commands using the command registry."""
        # Register all commands directly to the main app
        for command in self._command_registry.get_commands().values():
            self.add_command(
                command.func,
                name=command.name,
                help_text=command.help_text,
            )

    def _print_output(self, output: str, is_error: bool = False) -> None:
        # sourcery skip: hoist-similar-statement-from-if, hoist-statement-from-if
        """Print tool output with proper formatting for single/multi-line content."""
        if "\n" in output:
            # Multi-line output: start on new line
            cleaned_output = output.rstrip("\n")
            self.console.print()  # Start on new line
            if is_error:
                self.console.print(f"[red]{cleaned_output}[/red]")
            else:
                self.console.print(cleaned_output)
        else:
            # Single-line output: strip trailing newlines for clean inline display
            cleaned_output = output.rstrip("\n")
            if is_error:
                self.console.print(f"[red]{cleaned_output}[/red]")
            else:
                self.console.print(cleaned_output)

    def _run_tool_command(
        self,
        command: list[str],
        success_message: str,
        print_stderr_on_success: bool = False,
    ) -> bool:
        """Run a tool command and return success status.

        Returns
        -------
        bool
            True if command succeeded, False otherwise.
        """
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            if result.stdout:
                self._print_output(result.stdout)
            if print_stderr_on_success and result.stderr:
                self._print_output(result.stderr)
        except subprocess.CalledProcessError as e:
            if e.stdout:
                self._print_output(e.stdout)
            if e.stderr:
                self._print_output(e.stderr, is_error=True)
            return False
        except FileNotFoundError:
            self.rich.print_error(f"❌ Command not found: {command[0]}")
            return False
        else:
            self.rich.print_success(success_message)
            return True

    # ============================================================================
    # DEVELOPMENT COMMANDS
    # ============================================================================

    def lint(
        self,
        fix: Annotated[
            bool,
            Option("--fix", help="Automatically apply fixes"),
        ] = False,
    ) -> None:
        """Run linting checks with Ruff to ensure code quality."""
        self.rich.print_section("Running Linting", "blue")
        self.rich.print_info("Checking code quality with Ruff...")

        cmd = ["uv", "run", "ruff", "check"]
        if fix:
            cmd.append("--fix")
        cmd.append(".")

        success = self._run_tool_command(
            cmd,
            "Linting completed successfully",
        )
        if not success:
            self.rich.print_error("Linting did not pass - see issues above")
            sys.exit(1)

    def lint_fix(self) -> None:
        """Run linting checks with Ruff and automatically apply fixes."""
        self.rich.print_section("Running Linting with Fixes", "blue")
        success = self._run_tool_command(
            ["uv", "run", "ruff", "check", "--fix", "."],
            "Linting with fixes completed successfully",
        )
        if not success:
            self.rich.print_error(
                "Linting with fixes did not complete - see issues above",
            )
            sys.exit(1)

    def format_code(self) -> None:
        """Format code using Ruff's formatter for consistent styling."""
        self.rich.print_section("Formatting Code", "blue")
        success = self._run_tool_command(
            ["uv", "run", "ruff", "format", "."],
            "Code formatting completed successfully",
        )
        if not success:
            self.rich.print_error("Code formatting did not pass - see issues above")
            sys.exit(1)

    def type_check(self) -> None:
        """Perform static type checking using basedpyright."""
        self.rich.print_section("Type Checking", "blue")
        success = self._run_tool_command(
            ["uv", "run", "basedpyright"],
            "Type checking completed successfully",
        )
        if not success:
            self.rich.print_error("Type checking did not pass - see issues above")
            sys.exit(1)

    def lint_docstring(self) -> None:
        """Lint docstrings for proper formatting and completeness."""
        self.rich.print_section("Linting Docstrings", "blue")
        success = self._run_tool_command(
            ["uv", "run", "pydoclint", "--config=pyproject.toml", "."],
            "Docstring linting completed successfully",
            print_stderr_on_success=True,
        )
        if not success:
            self.rich.print_error("Docstring linting did not pass - see issues above")
            sys.exit(1)

    def docstring_coverage(self) -> None:
        """Check docstring coverage across the codebase."""
        self.rich.print_section("Docstring Coverage", "blue")
        self._run_tool_command(
            ["uv", "run", "docstr-coverage", "--verbose", "2", "."],
            "Docstring coverage report generated",
            print_stderr_on_success=True,
        )

    def pre_commit(self) -> None:
        """Run pre-commit hooks to ensure code quality before commits."""
        self.rich.print_section("Running Pre-commit Checks", "blue")
        success = self._run_tool_command(
            ["uv", "run", "pre-commit", "run", "--all-files"],
            "Pre-commit checks completed successfully",
        )
        if not success:
            self.rich.print_error("Pre-commit checks did not pass - see issues above")
            sys.exit(1)

    def _remove_item(self, item: Path, project_root: Path) -> tuple[int, int]:
        """Remove a file or directory and return (count, size).

        Parameters
        ----------
        item : Path
            File or directory to remove.
        project_root : Path
            Project root directory for relative path display.

        Returns
        -------
        tuple[int, int]
            Tuple of (items_removed, bytes_freed).
        """
        try:
            if item.is_file():
                size = item.stat().st_size
                item.unlink()
                self.console.print(
                    f"[dim]Removed: {item.relative_to(project_root)}[/dim]",
                )
                return (1, size)
            if item.is_dir():
                dir_size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                shutil.rmtree(item)
                self.console.print(
                    f"[dim]Removed: {item.relative_to(project_root)}/[/dim]",
                )
                return (1, dir_size)
        except OSError as e:
            self.rich.print_warning(
                f"Could not remove {item.relative_to(project_root)}: {e}",
            )
        return (0, 0)

    def _clean_empty_directories(self, project_root: Path) -> int:
        """Clean empty directories in tests/unit and scripts.

        Parameters
        ----------
        project_root : Path
            Project root directory.

        Returns
        -------
        int
            Number of directories removed.
        """
        cleaned = 0
        for dir_path in [project_root / "tests" / "unit", project_root / "scripts"]:
            if not dir_path.exists():
                continue

            for subdir in dir_path.iterdir():
                if not subdir.is_dir() or subdir.name in (
                    "__pycache__",
                    ".pytest_cache",
                ):
                    continue

                contents = list(subdir.iterdir())
                if not contents or all(
                    item.name == "__pycache__" and item.is_dir() for item in contents
                ):
                    try:
                        shutil.rmtree(subdir)
                        cleaned += 1
                        self.console.print(
                            f"[dim]Removed empty directory: {subdir.relative_to(project_root)}/[/dim]",
                        )
                    except OSError as e:
                        self.rich.print_warning(
                            f"Could not remove {subdir.relative_to(project_root)}: {e}",
                        )
        return cleaned

    def clean(self) -> None:
        """Clean temporary files, cache directories, and build artifacts."""
        self.rich.print_section("Cleaning Project", "blue")

        project_root = Path(__file__).parent.parent
        cleaned_count = 0
        total_size = 0

        # Patterns to clean
        patterns_to_clean = [
            # Python cache
            ("**/__pycache__", "Python cache directories"),
            ("**/*.pyc", "Python compiled files"),
            ("**/*.pyo", "Python optimized files"),
            ("**/*$py.class", "Python class files"),
            # Pytest cache
            (".pytest_cache", "Pytest cache directory"),
            # Coverage files
            (".coverage", "Coverage data file"),
            (".coverage.*", "Coverage data files"),
            # Ruff cache
            (".ruff_cache", "Ruff cache directory"),
            # Mypy cache
            (".mypy_cache", "Mypy cache directory"),
            # Build artifacts
            ("build", "Build directory"),
            ("dist", "Distribution directory"),
            ("*.egg-info", "Egg info directories"),
            # Test artifacts
            ("htmlcov", "HTML coverage reports"),
            ("coverage.xml", "Coverage XML report"),
            ("coverage.json", "Coverage JSON report"),
            ("lcov.info", "LCOV coverage report"),
            ("junit.xml", "JUnit XML report"),
            (".hypothesis", "Hypothesis cache"),
        ]

        # Directories to never clean
        protected_dirs = {".venv", "venv"}

        for pattern, description in patterns_to_clean:
            matches = list(project_root.glob(pattern))
            if not matches:
                continue

            # Filter out protected directories
            matches = [
                m
                for m in matches
                if all(protected not in str(m) for protected in protected_dirs)
            ]

            if not matches:
                continue

            self.rich.print_info(f"Cleaning {description}...")

            for item in matches:
                count, size = self._remove_item(item, project_root)
                cleaned_count += count
                total_size += size

        # Clean empty directories
        cleaned_count += self._clean_empty_directories(project_root)

        if cleaned_count > 0:
            size_mb = total_size / (1024 * 1024)
            self.rich.print_success(
                f"Cleaned {cleaned_count} item(s), freed {size_mb:.2f} MB",
            )
        else:
            self.rich.print_info("Nothing to clean - project is already clean!")

    def run_all_checks(
        self,
        fix: Annotated[
            bool,
            Option("--fix", help="Automatically fix issues where possible"),
        ] = False,
    ) -> None:
        """Run all development checks including linting, type checking, and documentation."""
        self.rich.print_section("Running All Development Checks", "blue")
        checks: list[tuple[str, Callable[[], None]]] = [
            ("Linting", self.lint_fix if fix else self.lint),
            ("Code Formatting", self.format_code),
            ("Type Checking", self.type_check),
            ("Docstring Linting", self.lint_docstring),
            ("Pre-commit Checks", self.pre_commit),
        ]

        results: list[tuple[str, bool]] = []

        # Run checks with progress bar
        with self.rich.create_progress_bar(
            "Running Development Checks",
            len(checks),
        ) as progress:
            task = progress.add_task("Running Development Checks", total=len(checks))

            for check_name, check_func in checks:
                progress.update(task, description=f"Running {check_name}...")
                progress.refresh()  # Force refresh to show the update

                try:
                    check_func()
                    results.append((check_name, True))
                except Exception:
                    results.append((check_name, False))
                    # Don't exit early, continue with other checks

                progress.advance(task)
                progress.refresh()  # Force refresh after advance

        # Add newline after progress bar completes
        self.console.print()

        # Summary using Rich table
        self.rich.print_section("Development Checks Summary", "blue")

        passed = sum(bool(success) for _, success in results)
        total = len(results)

        # Create Rich table for results
        table_data: list[tuple[str, str, str]] = [
            (
                check_name,
                "PASSED" if success else "FAILED",
                "Completed" if success else "Failed",
            )
            for check_name, success in results
        ]

        self.rich.print_rich_table(
            "",
            [("Check", "cyan"), ("Status", "green"), ("Details", "white")],
            table_data,
        )

        self.console.print()
        if passed == total:
            self.rich.print_success(f"All {total} checks passed!")
        else:
            self.rich.print_error(f"{passed}/{total} checks passed")
            sys.exit(1)


# Create the CLI app instance
app = DevCLI().app


def main() -> None:
    """Entry point for the development CLI script."""
    cli = DevCLI()
    cli.run()


if __name__ == "__main__":
    main()
