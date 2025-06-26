"""Test command group for Tux CLI.

This module provides all testing-related commands for the Tux project.
"""

from pathlib import Path

import click
from loguru import logger

from tux.cli.core import command_registration_decorator, create_group, run_command

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


# @command_registration_decorator(test_group, name="tasks")
# @click.option(
#     "--format",
#     "output_format",
#     type=click.Choice(["table", "json", "summary"], case_sensitive=False),
#     default="table",
#     help="Output format for task analysis",
# )
# @click.option(
#     "--save",
#     type=str,
#     help="Save analysis to file (e.g., --save=task_analysis.json)",
# )
# @click.option(
#     "--category",
#     type=str,
#     help="Analyze specific task category (SCHEDULED, GATEWAY, SYSTEM, COMMAND, UNKNOWN)",
# )
# @click.option(
#     "--recommendations",
#     is_flag=True,
#     help="Show limit recommendations based on usage patterns",
# )
# def analyze_tasks(
#     output_format: str,
#     save: str | None,
#     category: str | None,
#     recommendations: bool,
# ) -> int:
#     """Analyze runtime task usage patterns and provide rate limiting insights.

#     This command analyzes task usage data collected from a running bot instance
#     to help determine appropriate task monitoring thresholds and identify potential
#     performance issues.

#     Examples:
#         tux test tasks                          # Basic table view
#         tux test tasks --format=json           # JSON output
#         tux test tasks --recommendations       # Show limit recommendations
#         tux test tasks --save=analysis.json    # Save to file
#         tux test tasks --category=SCHEDULED    # Analyze specific category
#     """
#     try:
#         # Import here to avoid circular imports and allow CLI to work without bot running
#         # from tux.utils.task_manager import TaskManager, TaskCategory

#         # Note: In a real implementation, you'd need to connect to a running bot instance
#         # or read from a data file. For now, we'll show the structure and mock data.
#         analysis_data = _get_task_analysis_data()

#         if not analysis_data:
#             logger.error("No task analysis data available. Ensure the bot has been running to collect data.")
#             return 1

#         # Filter by category if specified
#         if category:
#             category = category.upper()
#             if category not in analysis_data.get("categories", {}):
#                 logger.error(
#                     f"Category '{category}' not found. Available: {list(analysis_data.get('categories', {}).keys())}",
#                 )
#                 return 1
#             analysis_data["categories"] = {category: analysis_data["categories"][category]}

#         # Display analysis
#         if output_format == "json":
#             _display_json_analysis(analysis_data)
#         elif output_format == "summary":
#             _display_summary_analysis(analysis_data, recommendations)
#         else:
#             _display_table_analysis(analysis_data, recommendations)

#         # Save to file if requested
#         if save:
#             _save_analysis_to_file(analysis_data, save)

#     except ImportError as e:
#         logger.error(f"Failed to import task manager: {e}")
#         logger.info("Task analysis requires the bot components to be available.")
#         return 1
#     except Exception as e:
#         logger.error(f"Task analysis failed: {e}")
#         return 1
#     else:
#         return 0


# def _get_task_analysis_data() -> dict[str, Any]:
#     """Get task analysis data from running bot or mock data for demo."""
#     # TODO: In a real implementation, this would:
#     # 1. Connect to running bot via IPC/Redis/file
#     # 2. Call task_manager.get_usage_analysis()
#     # 3. Return real data

#     # For now, return mock data to demonstrate the structure
#     return {
#         "collection_period_hours": 24,
#         "measurement_interval_minutes": 5,
#         "categories": {
#             "SCHEDULED": {
#                 "data_points": 288,
#                 "current_limit": 100,
#                 "peak_usage": 45,
#                 "average": 28.5,
#                 "median": 27,
#                 "p95": 42,
#                 "p99": 44,
#                 "recent_trend": "stable",
#                 "insights": ["✅ Usage is stable"],
#             },
#             "COMMAND": {
#                 "data_points": 288,
#                 "current_limit": 500,
#                 "peak_usage": 156,
#                 "average": 45.2,
#                 "median": 38,
#                 "p95": 120,
#                 "p99": 145,
#                 "recent_trend": "increasing",
#                 "insights": ["📈 Usage trending upward", "📊 High variability detected"],
#             },
#             "SYSTEM": {
#                 "data_points": 288,
#                 "current_limit": 200,
#                 "peak_usage": 67,
#                 "average": 23.1,
#                 "median": 22,
#                 "p95": 45,
#                 "p99": 58,
#                 "recent_trend": "stable",
#                 "insights": ["✅ Usage is stable"],
#             },
#         },
#         "overall_recommendations": [
#             "🔍 Monitor for at least 1 week before setting hard limits",
#             "📊 Focus on P95/P99 values rather than peaks for limit setting",
#             "⚡ Set limits at 2-3x your P99 usage to handle legitimate spikes",
#             "🔄 Review and adjust limits monthly based on growth patterns",
#         ],
#     }


# def _display_table_analysis(analysis_data: dict[str, Any], show_recommendations: bool) -> None:
#     """Display task analysis in table format."""
#     logger.info("📊 Task Usage Analysis")
#     logger.info("=" * 70)
#     logger.info(f"Collection Period: {analysis_data['collection_period_hours']} hours")
#     logger.info(f"Measurement Interval: {analysis_data['measurement_interval_minutes']} minutes")
#     logger.info("")

#     # Category analysis
#     for category_name, stats in analysis_data["categories"].items():
#         logger.info(f"🔍 {category_name}")
#         logger.info("-" * 40)
#         logger.info(f"  Data Points:     {stats['data_points']}")
#         logger.info(f"  Current Limit:   {stats['current_limit']}")
#         logger.info(f"  Peak Usage:      {stats['peak_usage']}")
#         logger.info(f"  Average:         {stats['average']}")
#         logger.info(f"  P95/P99:         {stats['p95']}/{stats['p99']}")
#         logger.info(f"  Recent Trend:    {stats['recent_trend']}")

#         if stats.get("insights"):
#             logger.info("  Insights:")
#             for insight in stats["insights"]:
#                 logger.info(f"    {insight}")

#         if show_recommendations:
#             recommended_limit = int(stats["p99"] * 2.5)
#             utilization = (stats["peak_usage"] / stats["current_limit"]) * 100
#             logger.info(f"  Utilization:     {utilization:.1f}%")
#             logger.info(f"  Recommended:     {recommended_limit} (2.5x P99)")

#         logger.info("")

#     # Overall recommendations
#     if show_recommendations:
#         logger.info("💡 General Recommendations:")
#         for rec in analysis_data["overall_recommendations"]:
#             logger.info(f"  {rec}")


# def _display_summary_analysis(analysis_data: dict[str, Any], show_recommendations: bool) -> None:
#     """Display condensed summary of task analysis."""
#     categories = analysis_data["categories"]
#     total_categories = len(categories)
#     stable_categories = sum(stats["recent_trend"] == "stable" for stats in categories.values())

#     logger.info("📊 Task Analysis Summary")
#     logger.info("=" * 40)
#     logger.info(f"Categories Monitored: {total_categories}")
#     logger.info(f"Stable Categories:    {stable_categories}")
#     logger.info(f"Data Quality:         {analysis_data['collection_period_hours']}h collection")
#     logger.info("")

#     # Quick stats
#     for category_name, stats in categories.items():
#         trend_emoji = {"stable": "✅", "increasing": "📈", "decreasing": "📉"}.get(stats["recent_trend"], "❓")
#         utilization = (stats["peak_usage"] / stats["current_limit"]) * 100
#         logger.info(
#             f"{trend_emoji} {category_name:10} | Peak: {stats['peak_usage']:3d} | P99: {stats['p99']:3d} | Util: {utilization:5.1f}%",
#         )

#     if show_recommendations:
#         logger.info("\n🎯 Quick Recommendations:")
#         if high_util_categories := [
#             name for name, stats in categories.items() if (stats["peak_usage"] / stats["current_limit"]) > 0.8
#         ]:
#             logger.info(f"  • Consider increasing limits for: {', '.join(high_util_categories)}")
#         else:
#             logger.info("  • Current limits appear adequate for observed usage")


# def _display_json_analysis(analysis_data: dict[str, Any]) -> None:
#     """Display task analysis as formatted JSON."""
#     logger.debug(json.dumps(analysis_data, indent=2))


# def _save_analysis_to_file(analysis_data: dict[str, Any], filename: str) -> None:
#     """Save analysis data to a file."""
#     try:
#         path = Path(filename)
#         path.parent.mkdir(parents=True, exist_ok=True)

#         with path.open("w") as f:
#             json.dump(analysis_data, f, indent=2)

#     except Exception as e:
#         logger.error(f"Failed to save analysis: {e}")
#     else:
#         logger.info(f"📄 Analysis saved to: {path.resolve()}")


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
    except Exception as e:
        logger.error(f"Failed to open HTML report: {e}")
        return 1
    else:
        logger.info("Opening HTML coverage report in browser...")
        return 0
