"""
Process Management Utilities for CLI.

Provides helpers for running shell commands and managing subprocesses.
"""

import os
import shlex
import subprocess

from scripts.ui import console, print_error


def run_command(
    command: list[str],
    capture_output: bool = True,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """
    Run a shell command and handle output.

    Parameters
    ----------
    command : list[str]
        The command and arguments to execute.
    capture_output : bool, optional
        Whether to capture stdout and stderr (default is True).
    check : bool, optional
        Whether to raise CalledProcessError if command fails (default is True).
    env : dict[str, str] | None, optional
        Custom environment variables. If None, uses a copy of os.environ.

    Returns
    -------
    subprocess.CompletedProcess[str]
        The result of the command execution.

    Raises
    ------
    subprocess.CalledProcessError
        If check is True and the command returns a non-zero exit code.
    """
    run_env = env if env is not None else os.environ.copy()

    # Log command for auditing
    console.print(f"[dim]Executing: {shlex.join(command)}[/dim]")

    try:
        result = subprocess.run(
            command,
            check=check,
            capture_output=capture_output,
            text=True,
            env=run_env,
        )

        if capture_output and result.stdout:
            # Use markup=False to avoid interpreting command output as Rich formatting
            console.print(result.stdout.strip(), markup=False)

    except subprocess.CalledProcessError as e:
        # Many tools (ruff, pyright) print errors to stdout
        if capture_output:
            if e.stdout:
                console.print(e.stdout.strip(), markup=False)
            if e.stderr:
                console.print(f"[red]{e.stderr.strip()}[/red]", markup=False)

        print_error(f"Command failed: {shlex.join(command)}")
        raise
    else:
        return result
