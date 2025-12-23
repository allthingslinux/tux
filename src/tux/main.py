"""Tux Discord Bot Main Entry Point."""

from tux.core.app import TuxApp


def run(debug: bool = False) -> int:
    """Instantiate and run the Tux application."""
    # The debug flag is currently used for logging info if needed,
    # but actual logging is configured by the CLI script.
    app = TuxApp()
    return app.run()
