#!/usr/bin/env python3
"""
Test CLI Script.

Testing operations management.
"""

import os
import sys
import webbrowser
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from typer import Argument, Option  # type: ignore[attr-defined]

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Note: Logging is configured by pytest via conftest.py
# No need to configure here as pytest will handle it

from scripts.base import BaseCLI, RichCLI
from scripts.registry import Command, CommandRegistry


class TestCLI(BaseCLI):
    """Testing operations management.

    Commands for running tests, generating coverage reports,
    parallel execution, HTML reports, and benchmarking.
    """

    def __init__(self):
        """Initialize the TestCLI application.

        Sets up the CLI with test-specific commands and configures
        the command registry for pytest operations.
        """
        # Don't call super().__init__() because we need no_args_is_help=False
        # Initialize BaseCLI components manually
        # Create Typer app directly with no_args_is_help=False for callback support
        self.app = typer.Typer(
            name="test",
            help="Testing operations",
            rich_markup_mode="rich",
            no_args_is_help=False,  # Allow callback to handle arguments
        )
        self.console = Console()
        self.rich = RichCLI()
        self._command_registry = CommandRegistry()
        self._setup_command_registry()
        self._setup_commands()
        self._setup_default_command()

    def _setup_command_registry(self) -> None:
        """Set up the command registry with all test commands."""
        # All commands directly registered without groups
        all_commands = [
            # Basic test commands
            Command(
                "all",
                self.all_tests,
                "Run all tests with coverage",
            ),
            Command("quick", self.quick_tests, "Run tests without coverage"),
            Command("plain", self.plain_tests, "Run tests with plain output"),
            Command("parallel", self.parallel_tests, "Run tests in parallel"),
            Command("html", self.html_report, "Generate HTML report"),
            Command(
                "coverage",
                self.coverage_report,
                "Generate coverage reports",
            ),
            Command("benchmark", self.benchmark_tests, "Run benchmark tests"),
        ]

        for cmd in all_commands:
            self._command_registry.register_command(cmd)

    def _setup_commands(self) -> None:
        """Set up all test CLI commands using the command registry."""
        # Register all commands directly to the main app
        for command in self._command_registry.get_commands().values():
            self.add_command(
                command.func,
                name=command.name,
                help_text=command.help_text,
            )

    def _setup_default_command(self) -> None:
        """Set up default command to handle test file paths."""

        @self.app.callback(invoke_without_command=True)
        def _default_callback(  # pyright: ignore[reportUnusedFunction]
            ctx: typer.Context,
            test_paths: Annotated[
                list[str] | None,
                Argument(help="Test file paths or test identifiers"),
            ] = None,
            coverage: Annotated[
                bool,
                Option("--coverage", "-c", help="Enable coverage collection"),
            ] = False,
        ) -> None:
            """Run tests with optional file paths.

            If no test paths are provided and no command is specified,
            runs all tests. By default, coverage is disabled for faster execution.
            Use --coverage to enable coverage collection.
            Test paths can be files, directories, or pytest node IDs.
            """
            if ctx.invoked_subcommand is None:
                self.rich.print_section("Running Tests", "blue")
                cmd = ["uv", "run", "pytest"]
                if not coverage:
                    cmd.append("--no-cov")
                if test_paths:
                    cmd.extend(test_paths)
                self._run_test_command(cmd, "Test run")

    def _run_test_command(self, command: list[str], description: str) -> bool:
        """Run a test command and return success status.

        Returns
        -------
        bool
            True if command succeeded, False otherwise.
        """
        try:
            self.rich.print_info(f"Running: {' '.join(command)}")
            # Use exec to replace the current process so signals are properly forwarded

            os.execvp(command[0], command)
        except FileNotFoundError:
            self.rich.print_error(f"Command not found: {command[0]}")
            return False
        except KeyboardInterrupt:
            self.rich.print_info("Test run interrupted")
            return False

    def _build_coverage_command(
        self,
        specific: str | None = None,
        format_type: str | None = None,
        quick: bool = False,
        fail_under: str | None = None,
    ) -> list[str]:
        """Build coverage command with various options.

        Returns
        -------
        list[str]
            Complete pytest command with coverage options.
        """
        # Start with base pytest command (coverage options come from pyproject.toml)
        cmd = ["uv", "run", "pytest"]

        # Handle specific path override
        if specific:
            cmd.append(f"--cov={specific}")

        # Handle coverage format overrides
        if quick:
            cmd.append("--cov-report=")
        elif format_type:
            match format_type:
                case "html":
                    cmd.append("--cov-report=html")
                case "xml":
                    cmd.append("--cov-report=xml:coverage.xml")
                case "json":
                    cmd.append("--cov-report=json")
                case _:
                    # For unsupported formats, let pyproject.toml handle it
                    pass

        # Handle fail-under override
        if fail_under:
            cmd.extend(["--cov-fail-under", fail_under])

        return cmd

    def _open_coverage_browser(self, format_type: str) -> None:
        """Open coverage report in browser if HTML format."""
        if format_type == "html":
            html_report_path = Path("docs/htmlcov/index.html")
            if html_report_path.exists():
                self.rich.print_info("Opening HTML coverage report in browser...")
                webbrowser.open(f"file://{html_report_path.resolve()}")

    # ============================================================================
    # TEST COMMANDS
    # ============================================================================

    def all_tests(
        self,
        test_paths: Annotated[
            list[str] | None,
            Argument(help="Test file paths or test identifiers"),
        ] = None,
    ) -> None:
        """Run all tests with coverage."""
        self.rich.print_section("Running Tests", "blue")
        cmd = ["uv", "run", "pytest"]
        if test_paths:
            cmd.extend(test_paths)
        self._run_test_command(cmd, "Test run")

    def quick_tests(
        self,
        test_paths: Annotated[
            list[str] | None,
            Argument(help="Test file paths or test identifiers"),
        ] = None,
    ) -> None:
        """Run tests without coverage (faster)."""
        self.rich.print_section("Quick Tests", "blue")
        cmd = ["uv", "run", "pytest", "--no-cov"]
        if test_paths:
            cmd.extend(test_paths)
        self._run_test_command(cmd, "Quick test run")

    def plain_tests(
        self,
        test_paths: Annotated[
            list[str] | None,
            Argument(help="Test file paths or test identifiers"),
        ] = None,
    ) -> None:
        """Run tests with plain output."""
        self.rich.print_section("Plain Tests", "blue")
        cmd = ["uv", "run", "pytest", "-p", "no:sugar"]
        if test_paths:
            cmd.extend(test_paths)
        self._run_test_command(cmd, "Plain test run")

    def parallel_tests(
        self,
        test_paths: Annotated[
            list[str] | None,
            Argument(help="Test file paths or test identifiers"),
        ] = None,
        workers: Annotated[
            int | None,
            Option(
                "--workers",
                "-n",
                help="Number of parallel workers (default: auto, uses CPU count)",
            ),
        ] = None,
        load_scope: Annotated[
            str | None,
            Option(
                "--load-scope",
                help="Load balancing scope: module, class, or function (default: module)",
            ),
        ] = None,
    ) -> None:
        """Run tests in parallel using pytest-xdist.

        Uses multiprocessing for true parallelism. Coverage is automatically
        combined across workers.

        Parameters
        ----------
        test_paths : list[str] | None
            Test file paths or test identifiers.
        workers : int | None
            Number of parallel workers. If None, uses 'auto' (CPU count).
        load_scope : str | None
            Load balancing scope. Options: 'module', 'class', 'function'.
            Default is 'module' for best performance.
        """
        self.rich.print_section("Parallel Tests (pytest-xdist)", "blue")
        cmd = ["uv", "run", "pytest"]

        # Add xdist options
        if workers is None:
            cmd.extend(["-n", "auto"])
        else:
            cmd.extend(["-n", str(workers)])

        # Add load balancing scope if specified
        if load_scope:
            cmd.extend(["--dist", load_scope])

        # Add test paths if provided
        if test_paths:
            cmd.extend(test_paths)

        self._run_test_command(cmd, "Parallel test run")

    def html_report(
        self,
        open_browser: Annotated[
            bool,
            Option("--open", help="Automatically open browser with HTML report"),
        ] = False,
    ) -> None:
        """Run tests and generate HTML report."""
        self.rich.print_section("HTML Report", "blue")
        cmd = [
            "uv",
            "run",
            "pytest",
            "--cov-report=html",
            "--html=reports/test_report.html",
            "--self-contained-html",
        ]
        if self._run_test_command(cmd, "HTML report generation") and open_browser:
            self._open_coverage_browser("html")

    def coverage_report(
        self,
        specific: Annotated[
            str | None,
            Option("--specific", help="Path to include in coverage"),
        ] = None,
        format_type: Annotated[
            str | None,
            Option("--format", help="Report format: html, xml, or json"),
        ] = None,
        quick: Annotated[
            bool,
            Option("--quick", help="Skip coverage report generation"),
        ] = False,
        fail_under: Annotated[
            str | None,
            Option("--fail-under", help="Minimum coverage percentage required"),
        ] = None,
        open_browser: Annotated[
            bool,
            Option(
                "--open",
                help="Automatically open browser for HTML coverage reports",
            ),
        ] = False,
    ) -> None:
        """Generate coverage reports."""
        self.rich.print_section("Coverage Report", "blue")

        cmd = self._build_coverage_command(specific, format_type, quick, fail_under)
        success = self._run_test_command(cmd, "Coverage report generation")

        if success and open_browser and format_type:
            self._open_coverage_browser(format_type)

    def benchmark_tests(self) -> None:
        """Run benchmark tests."""
        self.rich.print_section("Benchmark Tests", "blue")
        self._run_test_command(
            ["uv", "run", "pytest", "--benchmark-only", "--benchmark-sort=mean"],
            "Benchmark test run",
        )


# Create the CLI app instance
app = TestCLI().app


def main() -> None:
    """Entry point for the test CLI script."""
    cli = TestCLI()
    cli.run()


if __name__ == "__main__":
    main()
