"""Core utilities for Tux scripts."""

import subprocess
from typing import Any


def run_command(cmd: list[str], **kwargs: Any) -> int:
    """Run a command and return its exit code.

    Parameters
    ----------
    cmd : list[str]
        Command to run as a list of strings
    **kwargs : Any
        Additional arguments to pass to subprocess.run

    Returns
    -------
    int
        Exit code of the command (0 for success)
    """

    try:
        subprocess.run(cmd, check=True, **kwargs)

    except subprocess.CalledProcessError as e:
        return e.returncode

    else:
        return 0
