# events/on_command_completion.py

from discord.ext import commands

from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class OnCommandCompletion(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """
        Handles the event when a command is completed successfully.

        This function is called when a command is completed successfully.

        Args:
            ctx (commands.Context): The Context of the command.

        https://discordpy.readthedocs.io/en/stable/ext/commands/api.html#discord.discord.ext.commands.on_command_completion
        """  # noqa E501

        # For testing purposes only, remove this line later.
        await ctx.message.add_reaction("✅")
        logger.info(f"{ctx.author} used {ctx.command} in {ctx.channel}.")


async def setup(bot):
    await bot.add_cog(OnCommandCompletion(bot))
