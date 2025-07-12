"""Test command group for Tux CLI.

This module provides all testing-related commands for the Tux project.
"""

from pathlib import Path

import click
from loguru import logger

from cli.core import command_registration_decorator, create_group, run_command

# Create the test command group
test_group = create_group(
    "test",
    "Test commands for running various types of tests and generating reports.",
)


@command_registration_decorator(test_group, name="run")
def test() -> int:
    """Run tests with coverage and enhanced output."""
    return run_command(["pytest", "--cov=tux", "--cov-report=term-missing", "--randomly-seed=last"])


@command_registration_decorator(test_group, name="quick")
def test_quick() -> int:
    """Run tests without coverage (faster with enhanced output)."""
    return run_command(["pytest", "--no-cov", "--randomly-seed=last"])


@command_registration_decorator(test_group, name="plain")
def test_plain() -> int:
    """Run tests with plain output (no pytest-sugar)."""
    return run_command(["pytest", "-p", "no:sugar", "--cov=tux", "--cov-report=term-missing", "--randomly-seed=last"])


@command_registration_decorator(test_group, name="parallel")
def test_parallel() -> int:
    """Run tests in parallel using multiple workers."""
    return run_command(["pytest", "--cov=tux", "--cov-report=term-missing", "-n", "auto", "--randomly-seed=last"])


@command_registration_decorator(test_group, name="html")
def test_html() -> int:
    """Run tests and generate HTML report."""
    return run_command(
        [
            "pytest",
            "--cov=tux",
            "--cov-report=html",
            "--html=reports/test_report.html",
            "--self-contained-html",
            "--randomly-seed=last",
        ],
    )


@command_registration_decorator(test_group, name="benchmark")
def test_benchmark() -> int:
    """Run benchmark tests to measure performance."""
    return run_command(["pytest", "--benchmark-only", "--benchmark-sort=mean"])


@command_registration_decorator(test_group, name="coverage")
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
    "--open-browser",
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
@click.option(
    "--plain",
    is_flag=True,
    help="Use plain output (disable pytest-sugar)",
)
@click.option(
    "--xml-file",
    type=str,
    help="Custom XML filename (only with --format=xml, e.g., coverage-unit.xml)",
)
def coverage(
    report_format: str,
    fail_under: int | None,
    open_browser: bool,
    quick: bool,
    clean: bool,
    specific: str | None,
    plain: bool,
    xml_file: str | None,
) -> int:
    """Generate comprehensive coverage reports with various output formats."""
    # Clean coverage files if requested
    if clean:
        _clean_coverage_files()

    # Build and run command
    cmd = _build_coverage_command(specific, quick, report_format, fail_under, plain, xml_file)
    result = run_command(cmd)

    # Open HTML report if requested and generated
    if result == 0 and open_browser and report_format == "html":
        _open_html_report()

    return result


@command_registration_decorator(test_group, name="coverage-clean")
def coverage_clean() -> int:
    """Clean coverage files and data."""
    return _clean_coverage_files()


@command_registration_decorator(test_group, name="coverage-open")
def coverage_open() -> int:
    """Open HTML coverage report in browser."""
    return _open_html_report()


def _build_coverage_command(
    specific: str | None,
    quick: bool,
    report_format: str,
    fail_under: int | None,
    plain: bool = False,
    xml_file: str | None = None,
) -> list[str]:
    """Build the pytest coverage command with options."""
    cmd = ["pytest"]

    # Disable pytest-sugar if plain mode requested
    if plain:
        logger.info("Using plain output (pytest-sugar disabled)...")
        cmd.extend(["-p", "no:sugar"])

    # Set coverage path (specific or default)
    if specific:
        logger.info(f"Running coverage for specific path: {specific}")
        cmd.append(f"--cov={specific}")
    else:
        cmd.append("--cov=tux")

    # Handle quick mode (no reports)
    if quick:
        logger.info("Quick coverage check (no reports)...")
        cmd.append("--cov-report=")
        cmd.extend(["--randomly-seed=last"])  # Add randomization even for quick tests
        return cmd

    # Add report format
    _add_report_format(cmd, report_format, xml_file)

    # Add fail-under if specified
    if fail_under is not None:
        logger.info(f"Running with {fail_under}% coverage threshold...")
        cmd.extend(["--cov-fail-under", str(fail_under)])

    # Add randomization for reproducible test ordering
    cmd.extend(["--randomly-seed=last"])

    return cmd


def _add_report_format(cmd: list[str], report_format: str, xml_file: str | None = None) -> None:
    """Add the appropriate coverage report format to the command."""
    if report_format == "html":
        cmd.append("--cov-report=html")
        logger.info("Generating HTML coverage report...")
    elif report_format == "json":
        cmd.append("--cov-report=json")
        logger.info("Generating JSON coverage report...")
    elif report_format == "term":
        cmd.append("--cov-report=term-missing")
    elif report_format == "xml":
        if xml_file:
            cmd.append(f"--cov-report=xml:{xml_file}")
            logger.info(f"Generating XML coverage report: {xml_file}")
        else:
            cmd.append("--cov-report=xml")
            logger.info("Generating XML coverage report...")


def _clean_coverage_files() -> int:
    """Clean coverage files and directories."""
    import shutil  # noqa: PLC0415

    coverage_files = [
        ".coverage",
        ".coverage.*",
        "htmlcov/",
        "coverage.xml",
        "coverage.json",
    ]

    logger.info("🧹 Cleaning coverage files...")
    for pattern in coverage_files:
        if "*" in pattern:
            # Handle glob patterns
            for file_path in Path().glob(pattern):
                Path(file_path).unlink(missing_ok=True)
                logger.debug(f"Removed: {file_path}")
        else:
            path = Path(pattern)
            if path.is_file():
                path.unlink()
                logger.debug(f"Removed file: {path}")
            elif path.is_dir():
                shutil.rmtree(path, ignore_errors=True)
                logger.debug(f"Removed directory: {path}")

    logger.info("Coverage cleanup completed")
    return 0


def _open_html_report() -> int:
    """Open HTML coverage report in the default browser."""
    import webbrowser  # noqa: PLC0415

    html_report_path = Path("htmlcov/index.html")

    if not html_report_path.exists():
        logger.error("HTML coverage report not found. Run coverage with --format=html first.")
        return 1

    try:
        webbrowser.open(f"file://{html_report_path.resolve()}")
        logger.info("Opening HTML coverage report in browser...")
    except Exception as e:
        logger.error(f"Failed to open HTML report: {e}")
        return 1
    else:
        return 0
