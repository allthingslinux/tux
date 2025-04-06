"""Bot commands for the Tux CLI."""

from tux.cli.core import command_registration_decorator, create_group

# Create the bot command group
bot_group = create_group("bot", "Discord bot commands")


@command_registration_decorator(bot_group, name="start")
def start() -> int:
    """Start the Discord bot"""

    from tux.main import run

    return run()
