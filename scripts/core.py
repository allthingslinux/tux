"""
Core CLI Infrastructure.

Provides the foundation for all CLI scripts, including path setup,
environment loading, and a standardized Typer application factory.
"""

import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from typer import Typer

# ============================================================================
# BOOTSTRAP
# ============================================================================

# Ensure the 'src' directory is in the Python path so scripts can import 'tux'
ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Load .env file to make environment variables available to scripts and subprocesses
load_dotenv()


# ============================================================================
# FACTORY
# ============================================================================


def create_app(
    name: str | None = None,
    help_text: str | None = None,
    no_args_is_help: bool = True,
    **kwargs: Any,
) -> Typer:
    """
    Create a standardized Typer application.

    Parameters
    ----------
    name : str | None, optional
        The name of the CLI application or command group.
    help_text : str | None, optional
        Description text for the application.
    no_args_is_help : bool, optional
        Whether to show help if no arguments are provided (default is True).
    **kwargs : Any
        Additional arguments passed to the Typer constructor.

    Returns
    -------
    Typer
        A configured Typer application instance.
    """
    return Typer(
        name=name,
        help=help_text,
        rich_markup_mode="rich",
        no_args_is_help=no_args_is_help,
        **kwargs,
    )
