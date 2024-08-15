import discord
from discord.ext import commands
from loguru import logger

from tux.utils import checks


class Slowmode(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="slowmode",
        aliases=["sm"],
        usage="$slowmode [delay] <channel>",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def slowmode(
        self,
        ctx: commands.Context[commands.Bot],
        delay: str,
        channel: discord.TextChannel | discord.Thread | None = None,
    ) -> None:
        """
        Sets slowmode for the current channel or specified channel.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context of the command.
        delay : int
            The slowmode time in seconds, max is 21600.
        channel : discord.TextChannel | discord.Thread | None
            The channel to set the slowmode in.
        """

        if ctx.guild is None:
            return

        # If the channel is not specified, default to the current channe
        if channel is None:
            # Check if the current channel is a text channel
            if not isinstance(ctx.channel, discord.TextChannel | discord.Thread):
                await ctx.send(
                    "Invalid channel type, must be a text channel or thread.",
                    delete_after=30,
                    ephemeral=True,
                )
                return
            channel = ctx.channel

        # Unsure of how to type hint this properly as it can be a string or int
        # and I can't use a Union for the argument because discord.py nagging?
        try:
            if delay[-1] in ["s"]:
                delay = delay[:-1]
            if delay[-1] == "m":
                delay = delay[:-1]
                delay = int(delay) * 60  # type: ignore

            delay = int(delay)  # type: ignore
        except ValueError:
            await ctx.send("Invalid delay value, must be an integer.", delete_after=30, ephemeral=True)
            return

        if delay < 0 or delay > 21600:  # type: ignore
            await ctx.send("The slowmode delay must be between 0 and 21600 seconds.", delete_after=30, ephemeral=True)
            return

        try:
            await channel.edit(slowmode_delay=delay)  # type: ignore
            await ctx.send(f"Slowmode set to {delay} seconds in {channel.mention}.", delete_after=30, ephemeral=True)

        except Exception as error:
            await ctx.send(f"Failed to set slowmode. Error: {error}", delete_after=30, ephemeral=True)
            logger.error(f"Failed to set slowmode. Error: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Slowmode(bot))
