from contextlib import suppress

import discord
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.utils import checks


class Slowmode(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot

    # Channel type containing a list of all discord channel types that provide the edit() method and have the slowmode_delay attribute
    editable_channel = (
        discord.TextChannel | discord.VoiceChannel | discord.Thread | discord.StageChannel | discord.ForumChannel
    )

    @commands.hybrid_command(
        name="slowmode",
        aliases=["sm"],
        # only place where generate_usage shouldn't be used:
        usage="slowmode <delay|get> [channel]\nor slowmode [channel] <delay|get>",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def slowmode(
        self,
        ctx: commands.Context[Tux],
        first_arg: str,
        second_arg: str | None = None,
    ) -> None:
        """
        Set or get the slowmode for a channel.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        first_arg : str
            Either the delay, channel or 'get' command.
        second_arg : str
            Either the delay, channel or 'get' command.
        """

        assert ctx.guild

        action, channel = await self._parse_arguments(ctx, first_arg, second_arg)

        if not action or not channel:
            await ctx.send(
                "Invalid command usage. Please provide a valid delay or 'get' command.",
                ephemeral=True,
            )
            return

        if action.lower() in {"get", "g"}:
            await self._get_slowmode(ctx, channel)
        else:
            await self._set_slowmode(ctx, channel, action)

    async def _parse_arguments(
        self,
        ctx: commands.Context[Tux],
        first_arg: str,
        second_arg: str | None = None,
    ) -> tuple[str | None, editable_channel | None]:
        action = None
        channel = None

        channel_converter = commands.TextChannelConverter()
        with suppress(commands.CommandError):
            parsed_channel = await channel_converter.convert(ctx, first_arg)
            channel = parsed_channel

        if channel:
            action = second_arg
        else:
            action = first_arg
            if second_arg:
                with suppress(commands.CommandError):
                    parsed_channel = await channel_converter.convert(ctx, second_arg)
                    channel = parsed_channel

        if not channel:
            channel = self._get_channel(ctx)

        return action, channel

    @staticmethod
    def _get_channel(ctx: commands.Context[Tux]) -> editable_channel | None:
        return (
            ctx.channel
            if isinstance(
                ctx.channel,
                discord.TextChannel
                | discord.VoiceChannel
                | discord.Thread
                | discord.StageChannel
                | discord.ForumChannel,
            )
            else None
        )

    @staticmethod
    async def _get_slowmode(
        ctx: commands.Context[Tux],
        channel: editable_channel,
    ) -> None:
        try:
            await ctx.send(
                f"The slowmode for {channel.mention} is {channel.slowmode_delay} seconds.",
                ephemeral=True,
            )

        except Exception as error:
            await ctx.send(f"Failed to get slowmode. Error: {error}", ephemeral=True)
            logger.error(f"Failed to get slowmode. Error: {error}")

    async def _set_slowmode(
        self,
        ctx: commands.Context[Tux],
        channel: editable_channel,
        delay: str,
    ) -> None:
        delay_seconds = self._parse_delay(delay)

        if delay_seconds is None:
            await ctx.send("Invalid delay value, must be an integer.", ephemeral=True)
            return

        if not (0 <= delay_seconds <= 21600):
            await ctx.send(
                "The slowmode delay must be between 0 and 21600 seconds.",
                ephemeral=True,
            )
            return

        try:
            await channel.edit(slowmode_delay=delay_seconds)

            await ctx.send(
                f"Slowmode set to {delay_seconds} seconds in {channel.mention}.",
                ephemeral=True,
            )

        except Exception as error:
            await ctx.send(f"Failed to set slowmode. Error: {error}", ephemeral=True)
            logger.error(f"Failed to set slowmode. Error: {error}")

    @staticmethod
    def _parse_delay(delay: str) -> int | None:
        try:
            if delay.endswith("s"):
                delay = delay[:-1]
            elif delay.endswith("m"):
                delay = delay[:-1]
                return int(delay) * 60
            return int(delay)

        except ValueError:
            return None


async def setup(bot: Tux) -> None:
    await bot.add_cog(Slowmode(bot))
