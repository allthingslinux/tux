#!/usr/bin/env python3
"""
Development CLI Script

A unified interface for all development operations using the clean CLI infrastructure.
"""

import subprocess
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from scripts.base import BaseCLI
from scripts.registry import Command


class DevCLI(BaseCLI):
    """Development tools CLI with unified interface for all development operations."""

    def __init__(self):
        super().__init__(
            name="dev",
            description="Tux Development Tools CLI - A unified interface for all development operations",
        )
        self._setup_command_registry()
        self._setup_commands()

    def _setup_command_registry(self) -> None:
        """Setup the command registry with all development commands."""
        # All commands directly registered without groups
        all_commands = [
            # Code quality commands
            Command("lint", self.lint, "Run linting with Ruff to check code quality"),
            Command("lint-fix", self.lint_fix, "Run linting with Ruff and apply fixes"),
            Command("format", self.format_code, "Format code with Ruff"),
            Command("type-check", self.type_check, "Check types with basedpyright"),
            # Workflow commands
            Command("pre-commit", self.pre_commit, "Run pre-commit checks"),
            Command("all", self.run_all_checks, "Run all development checks"),
        ]

        for cmd in all_commands:
            self._command_registry.register_command(cmd)

    def _setup_commands(self) -> None:
        """Setup all development CLI commands using the command registry."""
        # Register all commands directly to the main app
        for command in self._command_registry.get_commands().values():
            self.add_command(
                command.func,
                name=command.name,
                help_text=command.help_text,
            )

    def _run_tool_command(self, command: list[str], success_message: str) -> bool:
        """Run a tool command and return success status."""
        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            if result.stdout:
                self.console.print(result.stdout)
        except subprocess.CalledProcessError as e:
            if e.stdout:
                self.console.print(e.stdout)
            if e.stderr:
                self.console.print(f"[red]{e.stderr}[/red]")
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

    def lint(self) -> None:
        self.rich.print_section("🔍 Running Linting", "blue")
        self.rich.print_info("Checking code quality with Ruff...")
        success = self._run_tool_command(["uv", "run", "ruff", "check", "."], "Linting completed successfully")
        if not success:
            self.rich.print_error("Linting failed - check output above for details")
            msg = "Linting failed"
            raise RuntimeError(msg)

    def lint_fix(self) -> None:
        self.rich.print_section("🔧 Running Linting with Fixes", "blue")
        success = self._run_tool_command(
            ["uv", "run", "ruff", "check", "--fix", "."],
            "Linting with fixes completed successfully",
        )
        if not success:
            self.rich.print_error("Linting with fixes failed - check output above for details")

    def format_code(self) -> None:
        self.rich.print_section("✨ Formatting Code", "blue")
        success = self._run_tool_command(["uv", "run", "ruff", "format", "."], "Code formatting completed successfully")
        if not success:
            self.rich.print_error("Code formatting failed - check output above for details")

    def type_check(self) -> None:
        self.rich.print_section("🔍 Type Checking", "blue")
        success = self._run_tool_command(["uv", "run", "basedpyright"], "Type checking completed successfully")
        if not success:
            self.rich.print_error("Type checking failed - check output above for details")
            msg = "Type checking failed"
            raise RuntimeError(msg)

    def pre_commit(self) -> None:
        self.rich.print_section("✅ Running Pre-commit Checks", "blue")
        success = self._run_tool_command(
            ["uv", "run", "pre-commit", "run", "--all-files"],
            "Pre-commit checks completed successfully",
        )
        if not success:
            self.rich.print_error("Pre-commit checks failed - check output above for details")
            msg = "Pre-commit checks failed"
            raise RuntimeError(msg)

    def run_all_checks(self) -> None:
        self.rich.print_section("🚀 Running All Development Checks", "blue")
        checks = [
            ("Linting", self.lint),
            ("Code Formatting", self.format_code),
            ("Type Checking", self.type_check),
            ("Pre-commit Checks", self.pre_commit),
        ]

        results = []

        # Run checks with progress bar
        with self.rich.create_progress_bar("Running Development Checks", len(checks)) as progress:
            task = progress.add_task("Running Development Checks", total=len(checks))

            for check_name, check_func in checks:
                progress.update(task, description=f"Running {check_name}...")

                try:
                    check_func()
                    results.append((check_name, True))
                except Exception:
                    results.append((check_name, False))
                    # Don't exit early, continue with other checks

                progress.advance(task)

        # Summary using Rich table
        self.rich.print_section("📊 Development Checks Summary", "blue")
        passed = sum(success for _, success in results)
        total = len(results)

        # Create Rich table for results
        self.rich.print_rich_table(
            "Check Results",
            [("Check", "cyan"), ("Status", "green"), ("Details", "white")],
            [
                (check_name, "✅ PASSED" if success else "❌ FAILED", "Completed" if success else "Failed")
                for check_name, success in results
            ],
        )

        self.console.print()
        if passed == total:
            self.rich.print_success(f"🎉 All {total} checks passed!")
        else:
            self.rich.print_error(f"⚠️ {passed}/{total} checks passed")
            sys.exit(1)


# Create the CLI app instance for mkdocs-typer
app = DevCLI().app


def main() -> None:
    """Entry point for the development CLI script."""
    cli = DevCLI()
    cli.run()


if __name__ == "__main__":
    main()
