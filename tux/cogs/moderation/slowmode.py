import discord
from discord.ext import commands
from loguru import logger

import tux.utils.checks as checks


class Slowmode(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="slowmode",
        aliases=["sm"],
        usage="$slowmode [delay: int] <channel>",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def slowmode(
        self,
        ctx: commands.Context[commands.Bot],
        delay: int,
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
                await ctx.reply("Invalid channel type, must be a text channel.", delete_after=10, ephemeral=True)
                return
            channel = ctx.channel

        if delay < 0 or delay > 21600:
            await ctx.reply("The slowmode delay must be between 0 and 21600 seconds.", delete_after=10, ephemeral=True)

        try:
            await channel.edit(slowmode_delay=delay)
            await ctx.reply(f"Slowmode set to {delay} seconds in {channel.mention}.", delete_after=10, ephemeral=True)

        except Exception as error:
            await ctx.reply(f"Failed to set slowmode. Error: {error}", delete_after=10, ephemeral=True)
            logger.error(f"Failed to set slowmode. Error: {error}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Slowmode(bot))
