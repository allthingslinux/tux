# main.py
import os

import discord
from cog_loader import CogLoader
from discord.ext import commands
from dotenv import load_dotenv
from utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)
load_dotenv()

from discord.ext import commands
from error_handler import ErrorHandler


async def setup(bot: commands.Bot, debug: bool = False):
    """
    Set up the bot including loading cogs and other necessary setup tasks.
    """
    await CogLoader.setup(bot, debug)
    logger.debug("Event handler setup completed.")


async def main():
    bot_prefix = ">"
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix=bot_prefix, intents=intents)

    await setup(bot, debug=True)

    @bot.command(name="sync")
    @commands.has_permissions(administrator=True)
    async def sync(ctx: commands.Context):
        """Syncs the slash command tree. This command is only available to administrators.

        Args:
            ctx (commands.Context): The invocation context sent by the Discord API which contains information
            about the command and from where it was called.
        """  # noqa E501

        if ctx.guild:
            bot.tree.copy_global_to(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        logger.info(f"{ctx.author} synced the slash command tree.")

    @bot.command(name="clear")
    @commands.has_permissions(administrator=True)
    async def clear(ctx: commands.Context):
        """Clears the slash command tree. This command is only available to administrators.

        Args:
            ctx (commands.Context): The invocation context sent by the Discord API which contains information
            about the command and from where it was called.
        """  # noqa E501

        bot.tree.clear_commands(guild=ctx.guild)
        if ctx.guild:
            bot.tree.copy_global_to(guild=ctx.guild)
        await bot.tree.sync(guild=ctx.guild)
        logger.info(f"{ctx.author} cleared the slash command tree.")

    @bot.event
    async def on_command_error(ctx: commands.Context, error):
        """Handles the event when a command has been invoked but an error has occurred.

        Args:
            ctx (commands.Context): The invocation context sent by the Discord API which contains information
            about the command and from where it was called.

            error (Exception): The error that occurred.
        """  # noqa E501
        if isinstance(error, commands.CommandNotFound):
            await ErrorHandler.handle_command_not_found(ctx, error)
        elif isinstance(error, commands.MissingPermissions):
            await ErrorHandler.handle_missing_permissions(ctx, error)
        elif isinstance(error, commands.BotMissingPermissions):
            await ErrorHandler.handle_bot_missing_permissions(ctx, error)
        else:
            await ErrorHandler.handle_other_errors(ctx, error)

    @bot.event
    async def on_command_completion(ctx: commands.Context):
        """Handles the event when a command has been completed its invocation. This event is called only if the command succeeded, i.e. all checks have passed and the user input it correctly.

        Args:
            ctx (commands.Context): The invocation context sent by the Discord API which contains information
            about the command and from where it was called.
        """  # noqa E501
        await ctx.message.add_reaction("✅")
        logger.info(f"{ctx.author} successfully executed {ctx.command}.")

    @bot.event
    async def on_ready():
        """
        Called when the client is done preparing the data received from Discord.
        Usually after login is successful and the Client.guilds and co. are filled up.
        """
        logger.info(f"{bot.user} has connected to Discord!", __name__)

    await bot.start(os.getenv("TOKEN") or "", reconnect=True)


if __name__ == "__main__":
    import asyncio

    # Run the main function
    asyncio.run(main())
