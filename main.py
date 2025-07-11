"""Entrypoint for the Tux Discord bot application."""

from core.app import TuxApp


def run() -> None:
    """
    Instantiate and run the Tux application.

    This function is the entry point for the Tux application.
    It creates an instance of the TuxApp class and runs it.
    """

    app = TuxApp()
    app.run()


if __name__ == "__main__":
    run()
