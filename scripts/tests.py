#!/usr/bin/env python3
"""
Test CLI Script.

A unified interface for all testing operations using the clean CLI infrastructure.
"""

import os
import sys
import webbrowser
from pathlib import Path
from typing import Annotated

from typer import Option  # type: ignore[attr-defined]

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Note: Logging is configured by pytest via conftest.py
# No need to configure here as pytest will handle it

from scripts.base import BaseCLI
from scripts.registry import Command


class TestCLI(BaseCLI):
    """Test CLI with unified interface for all testing operations.

    Provides comprehensive testing commands including coverage reports,
    parallel execution, HTML reports, and benchmarking capabilities.
    """

    def __init__(self):
        """Initialize the TestCLI application.

        Sets up the CLI with test-specific commands and configures
        the command registry for pytest operations.
        """
        super().__init__(name="test", description="Test CLI - A unified interface for all testing operations")
        self._setup_command_registry()
        self._setup_commands()

    def _setup_command_registry(self) -> None:
        """Set up the command registry with all test commands."""
        # All commands directly registered without groups
        all_commands = [
            # Basic test commands
            Command("run", self.run_tests, "Run tests with coverage and enhanced output"),
            Command("quick", self.quick_tests, "Run tests without coverage (faster)"),
            Command("plain", self.plain_tests, "Run tests with plain output"),
            Command("parallel", self.parallel_tests, "Run tests in parallel"),
            # Report commands
            Command("html", self.html_report, "Run tests and generate HTML report"),
            Command("coverage", self.coverage_report, "Generate comprehensive coverage reports"),
            # Specialized commands
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
            self.rich.print_error(f"❌ Command not found: {command[0]}")
            return False
        except KeyboardInterrupt:
            self.rich.print_info("🛑 Test run interrupted")
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
            html_report_path = Path("htmlcov/index.html")
            if html_report_path.exists():
                self.rich.print_info("🌐 Opening HTML coverage report in browser...")
                webbrowser.open(f"file://{html_report_path.resolve()}")

    # ============================================================================
    # TEST COMMANDS
    # ============================================================================

    def run_tests(self) -> None:
        """Run tests with coverage and enhanced output."""
        self.rich.print_section("🧪 Running Tests", "blue")
        self._run_test_command(["uv", "run", "pytest"], "Test run")

    def quick_tests(self) -> None:
        """Run tests without coverage (faster)."""
        self.rich.print_section("⚡ Quick Tests", "blue")
        self._run_test_command(["uv", "run", "pytest", "--no-cov"], "Quick test run")

    def plain_tests(self) -> None:
        """Run tests with plain output."""
        self.rich.print_section("📝 Plain Tests", "blue")
        self._run_test_command(["uv", "run", "pytest", "-p", "no:sugar"], "Plain test run")

    def parallel_tests(self) -> None:
        """Run tests in parallel."""
        self.rich.print_section("🔄 Parallel Tests", "blue")
        self._run_test_command(["uv", "run", "pytest", "-n", "auto"], "Parallel test run")

    def html_report(self) -> None:
        """Run tests and generate HTML report."""
        self.rich.print_section("🌐 HTML Report", "blue")
        cmd = [
            "uv",
            "run",
            "pytest",
            "--cov-report=html",
            "--html=reports/test_report.html",
            "--self-contained-html",
        ]
        if self._run_test_command(cmd, "HTML report generation"):
            self._open_coverage_browser("html")

    def coverage_report(
        self,
        specific: Annotated[str | None, Option(help="Specific path to include in coverage")] = None,
        format_type: Annotated[str | None, Option(help="Coverage report format: html, xml, or json")] = None,
        quick: Annotated[bool, Option(help="Quick run without generating coverage report")] = False,
        fail_under: Annotated[str | None, Option(help="Fail if coverage percentage is below this value")] = None,
        open_browser: Annotated[
            bool,
            Option(help="Automatically open browser for HTML coverage reports"),
        ] = False,
    ) -> None:
        """Generate comprehensive coverage reports."""
        self.rich.print_section("📈 Coverage Report", "blue")

        cmd = self._build_coverage_command(specific, format_type, quick, fail_under)
        success = self._run_test_command(cmd, "Coverage report generation")

        if success and open_browser and format_type:
            self._open_coverage_browser(format_type)

    def benchmark_tests(self) -> None:
        """Run benchmark tests."""
        self.rich.print_section("📊 Benchmark Tests", "blue")
        self._run_test_command(
            ["uv", "run", "pytest", "--benchmark-only", "--benchmark-sort=mean"],
            "Benchmark test run",
        )


# Create the CLI app instance for mkdocs-typer
app = TestCLI().app


def main() -> None:
    """Entry point for the test CLI script."""
    cli = TestCLI()
    cli.run()


if __name__ == "__main__":
    main()
