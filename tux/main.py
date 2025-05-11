"""Entrypoint for the Tux Discord bot application."""

from tux.app import TuxApp


def run() -> None:
    """Instantiate and run the Tux application."""
    app = TuxApp()
    app.run()


if __name__ == "__main__":
    run()
