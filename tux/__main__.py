"""Entry point for running Tux as a module.

This module allows running Tux using 'python -m tux'.
It provides access to all Tux commands through the CLI interface.
"""

import sys

from tux.cli import main

if __name__ == "__main__":
    sys.exit(main())
