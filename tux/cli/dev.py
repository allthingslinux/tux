"""Development tools and utilities for Tux."""

import shutil
import webbrowser
from pathlib import Path

import click
from loguru import logger

from tux.cli.core import (
    command_registration_decorator,
    create_group,
    run_command,
)

# Create the dev command group
dev_group = create_group("dev", "Development tools")


@command_registration_decorator(dev_group, name="lint")
def lint() -> int:
    """Run linting with Ruff."""
    return run_command(["ruff", "check", "."])


@command_registration_decorator(dev_group, name="lint-fix")
def lint_fix() -> int:
    """Run linting with Ruff and apply fixes."""
    return run_command(["ruff", "check", "--fix", "."])


@command_registration_decorator(dev_group, name="format")
def format_code() -> int:
    """Format code with Ruff."""
    return run_command(["ruff", "format", "."])


@command_registration_decorator(dev_group, name="type-check")
def type_check() -> int:
    """Check types with Pyright."""
    return run_command(["pyright"])


@command_registration_decorator(dev_group, name="pre-commit")
def check() -> int:
    """Run pre-commit checks."""
    return run_command(["pre-commit", "run", "--all-files"])


@command_registration_decorator(dev_group, name="test")
def test() -> int:
    """Run tests with coverage."""
    return run_command(["pytest", "--cov=tux", "--cov-report=term-missing"])


@command_registration_decorator(dev_group, name="test-quick")
def test_quick() -> int:
    """Run tests without coverage (faster)."""
    return run_command(["pytest", "--no-cov"])


def _build_coverage_command(specific: str | None, quick: bool, report_format: str, fail_under: int | None) -> list[str]:
    """Build the pytest coverage command with options."""
    cmd = ["pytest"]

    # Set coverage path (specific or default)
    if specific:
        logger.info(f"🔍 Running coverage for specific path: {specific}")
        cmd.append(f"--cov={specific}")
    else:
        cmd.append("--cov=tux")

    # Handle quick mode (no reports)
    if quick:
        logger.info("⚡ Quick coverage check (no reports)...")
        cmd.append("--cov-report=")
        return cmd

    # Add report format
    _add_report_format(cmd, report_format)

    # Add fail-under if specified
    if fail_under is not None:
        logger.info(f"🎯 Running with {fail_under}% coverage threshold...")
        cmd.extend(["--cov-fail-under", str(fail_under)])

    return cmd


def _add_report_format(cmd: list[str], report_format: str) -> None:
    """Add report format option to command."""
    match report_format:
        case "term":
            logger.info("🏃 Running tests with terminal coverage report...")
            cmd.append("--cov-report=term-missing")
        case "html":
            logger.info("📊 Generating HTML coverage report...")
            cmd.append("--cov-report=html")
        case "xml":
            logger.info("📄 Generating XML coverage report...")
            cmd.append("--cov-report=xml")
        case "json":
            logger.info("📋 Generating JSON coverage report...")
            cmd.append("--cov-report=json")
        case _:
            # Default case - should not happen due to click choices
            cmd.append("--cov-report=term-missing")


def _handle_post_coverage_actions(result: int, report_format: str, open_browser: bool) -> None:
    """Handle post-command actions after coverage run."""
    if result != 0:
        return

    match report_format:
        case "html":
            logger.success("✅ HTML report generated at: htmlcov/index.html")
            if open_browser:
                logger.info("🌐 Opening HTML coverage report...")
                try:
                    webbrowser.open("htmlcov/index.html")
                except Exception:
                    logger.warning("Could not open browser. HTML report is available at htmlcov/index.html")
        case "xml":
            logger.success("✅ XML report generated at: coverage.xml")
        case "json":
            logger.success("✅ JSON report generated at: coverage.json")
        case _:
            # For terminal or other formats, no specific post-action needed
            pass


@command_registration_decorator(dev_group, name="coverage")
@click.option(
    "--format",
    "report_format",
    type=click.Choice(["term", "html", "xml", "json"], case_sensitive=False),
    default="term",
    help="Coverage report format",
)
@click.option(
    "--fail-under",
    type=click.IntRange(0, 100),
    help="Fail if coverage is below this percentage",
)
@click.option(
    "--open",
    is_flag=True,
    help="Open HTML report in browser (only with --format=html)",
)
@click.option(
    "--quick",
    is_flag=True,
    help="Quick coverage check without generating reports",
)
@click.option(
    "--clean",
    is_flag=True,
    help="Clean coverage files before running",
)
@click.option(
    "--specific",
    type=str,
    help="Run coverage for specific path (e.g., tux/utils)",
)
def coverage(
    report_format: str,
    fail_under: int | None,
    open: bool,  # noqa: A002
    quick: bool,
    clean: bool,
    specific: str | None,
) -> int:
    """Generate coverage reports with various options."""
    # Clean first if requested
    if clean:
        logger.info("🧹 Cleaning coverage files...")
        coverage_clean()

    # Build and run command
    cmd = _build_coverage_command(specific, quick, report_format, fail_under)
    result = run_command(cmd)

    # Handle post-command actions
    _handle_post_coverage_actions(result, report_format, open)

    return result


@command_registration_decorator(dev_group, name="coverage-clean")
def coverage_clean() -> int:
    """Clean coverage files and reports."""
    logger.info("🧹 Cleaning coverage files...")

    files_to_remove = [".coverage", "coverage.xml", "coverage.json"]
    dirs_to_remove = ["htmlcov"]

    # Remove individual files
    for file_name in files_to_remove:
        file_path = Path(file_name)
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Removed {file_name}")
        except OSError as e:
            logger.error(f"Error removing {file_name}: {e}")

    # Remove directories
    for dir_name in dirs_to_remove:
        dir_path = Path(dir_name)
        try:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                logger.info(f"Removed {dir_name}")
        except OSError as e:
            logger.error(f"Error removing {dir_name}: {e}")

    # Remove .coverage.* pattern files using Path.glob
    cwd = Path()
    for coverage_file in cwd.glob(".coverage.*"):
        try:
            coverage_file.unlink()
            logger.info(f"Removed {coverage_file.name}")
        except OSError as e:
            logger.error(f"Error removing {coverage_file.name}: {e}")

    logger.success("✅ Coverage files cleaned")
    return 0


@command_registration_decorator(dev_group, name="coverage-open")
def coverage_open() -> int:
    """Open HTML coverage report in browser."""
    html_report = Path("htmlcov/index.html")

    if not html_report.exists():
        logger.error("❌ HTML report not found. Run 'poetry run tux dev coverage --format=html' first")
        return 1

    logger.info("🌐 Opening HTML coverage report...")
    try:
        webbrowser.open(str(html_report))
    except Exception as e:
        logger.error(f"Could not open browser: {e}")
        logger.info(f"HTML report is available at: {html_report}")
        return 1
    else:
        logger.success("✅ Coverage report opened in browser")
        return 0
