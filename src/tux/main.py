"""Tux Discord Bot Main Entry Point."""

from tux.core.app import TuxApp


def run() -> int:
    """Instantiate and run the Tux application."""
    app = TuxApp()
    return app.run()
