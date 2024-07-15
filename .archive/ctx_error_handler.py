import contextlib
import sys
import traceback

import discord
from discord.ext import commands


class ContextCommandErrorHandler(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context[commands.Bot], error: Exception) -> None:
        """
        Handles errors that occur during command execution.

        Args:
            ctx: The context in which the error occurred.
            error: The exception that was raised.

        Returns
            None

        Raises
            None
        """

        # If the command has its own error handler, or the cog has its own error handler, return
        if hasattr(ctx.command, "on_error") or (
            ctx.cog and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None
        ):
            return

        # Ignore these errors
        ignored = (commands.CommandNotFound,)

        # Get the original exception if it exists
        error = getattr(error, "original", error)

        # If the error is in the ignored tuple, return
        if isinstance(error, ignored):
            return

        # If the command has been disabled, send a reply to the user
        if isinstance(error, commands.DisabledCommand):
            await ctx.send(f"{ctx.command} has been disabled.")

        # Private message error
        elif isinstance(error, commands.NoPrivateMessage):
            with contextlib.suppress(discord.HTTPException):
                await ctx.author.send(f"{ctx.command} can not be used in Private Messages.")

        # elif isinstance(error, commands.BadArgument):
        #     if ctx.command and ctx.command.qualified_name == "tag list":
        #         await ctx.send("I could not find that member. Please try again.")

        else:
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


async def setup(bot: commands.Bot):
    await bot.add_cog(ContextCommandErrorHandler(bot))
