"""
Command: dev profile.

Performance profiling utilities using cProfile for identifying bottlenecks.
"""

import cProfile
import pstats
from collections.abc import Callable
from io import StringIO
from pathlib import Path
from typing import Annotated, Any

from typer import Argument, Exit, Option

from scripts.core import create_app
from scripts.ui import print_error, print_section, print_success, rich_print

app = create_app()


def profile_function(
    func: Callable[..., Any],
    *args: Any,
    **kwargs: Any,
) -> tuple[Any, str]:
    """
    Profile a function execution and return result with profiling report.

    Parameters
    ----------
    func : Callable[..., Any]
        Function to profile.
    *args : Any
        Positional arguments to pass to function.
    **kwargs : Any
        Keyword arguments to pass to function.

    Returns
    -------
    tuple[Any, str]
        Function result and profiling report string.
    """
    profiler = cProfile.Profile()
    profiler.enable()
    try:
        result = func(*args, **kwargs)
    finally:
        profiler.disable()

    s = StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats("cumulative")
    ps.print_stats(20)  # Top 20 functions by cumulative time
    report = s.getvalue()

    return result, report


def profile_script(
    script_path: Path,
    output_file: Path | None = None,
    sort_by: str = "cumulative",
    lines: int = 20,
) -> None:
    """
    Profile a Python script execution.

    Parameters
    ----------
    script_path : Path
        Path to the Python script to profile.
    output_file : Path | None, optional
        Path to save profiling output. If None, prints to stdout.
    sort_by : str, optional
        Sort statistics by this metric. Options: 'cumulative', 'time', 'calls'.
        Defaults to 'cumulative'.
    lines : int, optional
        Number of lines to show in report. Defaults to 20.
    """
    if not script_path.exists():
        print_error(f"Script not found: {script_path}")
        raise Exit(1)

    profiler = cProfile.Profile()
    profiler.enable()

    try:
        # Execute the script
        exec(script_path.read_text(), {"__file__": str(script_path)})
    except Exception as e:
        print_error(f"Error executing script: {e}")
        raise Exit(1) from e
    finally:
        profiler.disable()

    # Generate report
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats(sort_by)
    ps.print_stats(lines)
    report = s.getvalue()

    if output_file:
        output_file.write_text(report)
        print_success(f"Profile report saved to: {output_file}")
    else:
        rich_print(f"\n[bold]Profiling Report for {script_path.name}[/bold]")
        rich_print(f"[dim]{'=' * 60}[/dim]")
        rich_print(report)


@app.command()
def profile(
    script: Annotated[
        Path,
        Argument(help="Path to Python script to profile"),
    ],
    output: Annotated[
        Path | None,
        Option("--output", "-o", help="Save profile report to file"),
    ] = None,
    sort_by: Annotated[
        str,
        Option("--sort", "-s", help="Sort by: cumulative, time, or calls"),
    ] = "cumulative",
    lines: Annotated[
        int,
        Option("--lines", "-n", help="Number of lines to show"),
    ] = 20,
) -> None:
    """
    Profile a Python script using cProfile.

    Examples
    --------
        uv run dev profile src/tux/core/bot.py
        uv run dev profile --output profile.txt --sort time --lines 50 script.py
    """
    print_section("Performance Profiling")
    profile_script(script, output, sort_by, lines)


if __name__ == "__main__":
    app()
