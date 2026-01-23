"""
Channel slowmode management commands.

This module provides functionality to set, modify, and remove slowmode
from Discord text channels, threads, and voice channels to control message rates.
"""

from contextlib import suppress

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.core.checks import requires_command_permission

# Type for channels that support slowmode
SlowmodeChannel = (
    discord.TextChannel
    | discord.Thread
    | discord.VoiceChannel
    | discord.ForumChannel
    | discord.StageChannel
)


class Slowmode(BaseCog):
    """Discord cog for managing channel slowmode settings."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the slowmode cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    @commands.hybrid_command(
        name="slowmode",
        aliases=["sm"],
        usage="slowmode [channel] [seconds]",
    )
    @commands.guild_only()
    @requires_command_permission()
    async def slowmode(
        self,
        ctx: commands.Context[Tux],
        channel_or_delay: str | None = None,
        delay: str | None = None,
    ) -> None:
        """
        Set or get the slowmode for a channel.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        channel_or_delay : Optional[str]
            Either a channel mention/ID or a delay value.
        delay : Optional[str]
            A delay value if channel_or_delay was a channel.

        Examples
        --------
        $slowmode - Get slowmode for current channel
        $slowmode 10 - Set 10 second slowmode in current channel
        $slowmode 5s - Set 5 second slowmode in current channel
        $slowmode 2m - Set 2 minute slowmode in current channel
        $slowmode 0 - Turn off slowmode in current channel
        $slowmode #general - Get slowmode for #general
        $slowmode #general 10 - Set 10 second slowmode in #general
        """
        assert ctx.guild

        # Defer early to acknowledge interaction before async work
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        # Try to parse first argument as a channel
        target_channel = (
            await self._resolve_channel(ctx, channel_or_delay)
            if channel_or_delay
            else None
        )

        # If first argument was a channel, use second argument as delay
        delay_value = delay if target_channel else channel_or_delay

        # If no channel specified, use current channel
        target_channel = target_channel or ctx.channel

        # Ensure target_channel is a type that supports slowmode
        if not isinstance(
            target_channel,
            discord.TextChannel
            | discord.Thread
            | discord.VoiceChannel
            | discord.ForumChannel
            | discord.StageChannel,
        ):
            await Slowmode._send_response(
                ctx,
                f"Slowmode cannot be set for this type of channel ({type(target_channel).__name__}).",
            )
            return

        # Now we have target_channel and maybe delay_value

        # If no delay value, get the current slowmode
        if not delay_value:
            await self._get_slowmode(ctx, target_channel)
        else:
            # Otherwise, set the slowmode
            await self._set_slowmode(ctx, target_channel, delay_value)

    async def _resolve_channel(
        self,
        ctx: commands.Context[Tux],
        value: str,
    ) -> discord.abc.GuildChannel | discord.Thread | None:
        """
        Resolve a channel using fast cached lookups first, then converter fallback.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        value : str
            The channel identifier (ID, mention, or name).

        Returns
        -------
        discord.abc.GuildChannel | discord.Thread | None
            The resolved channel if found, None otherwise.
        """
        assert ctx.guild

        # Fast path: Try cached lookup first for IDs and mentions (no API calls)
        if value.isdigit():
            # Channel ID - use cached lookup
            channel_id = int(value)
            return ctx.guild.get_channel(channel_id) or ctx.guild.get_thread(channel_id)

        if value.startswith("<#") and value.endswith(">"):
            # Channel mention - extract ID and use cached lookup
            with suppress(ValueError):
                channel_id = int(value[2:-1])
                return ctx.guild.get_channel(channel_id) or ctx.guild.get_thread(
                    channel_id,
                )

        # Fallback to converter if fast path didn't work
        with suppress(commands.CommandError):
            return await commands.GuildChannelConverter().convert(ctx, value)

        return None

    @staticmethod
    def _channel_supports_slowmode(channel: SlowmodeChannel) -> bool:
        """
        Check if a channel supports slowmode.

        Parameters
        ----------
        channel : SlowmodeChannel
            The channel to check

        Returns
        -------
        bool
            True if the channel supports slowmode, False otherwise
        """
        return hasattr(channel, "slowmode_delay") and callable(
            getattr(channel, "edit", None),
        )

    @staticmethod
    async def _send_response(
        ctx: commands.Context[Tux],
        content: str,
        *,
        ephemeral: bool = True,
    ) -> None:
        """
        Send a response message, handling both slash and prefix commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        content : str
            The message content to send.
        ephemeral : bool, optional
            Whether the message should be ephemeral (slash commands only), by default True.
        """
        if ctx.interaction:
            await ctx.interaction.followup.send(content, ephemeral=ephemeral)
        else:
            await ctx.send(content)

    @staticmethod
    def _format_slowmode_message(delay: int, channel_mention: str) -> str:
        """
        Format slowmode delay into a readable message.

        Returns
        -------
        str
            Formatted slowmode status message.
        """
        if delay == 0:
            return f"Slowmode is disabled in {channel_mention}."
        if delay == 1:
            return f"The slowmode in {channel_mention} is 1 second."
        if delay < 60:
            return f"The slowmode in {channel_mention} is {delay} seconds."
        if delay == 60:
            return f"The slowmode in {channel_mention} is 1 minute."

        minutes, seconds = divmod(delay, 60)
        if seconds == 0:
            return f"The slowmode in {channel_mention} is {minutes} minutes."
        minute_suffix = "s" if minutes > 1 else ""
        second_suffix = "s" if seconds > 1 else ""

        return f"The slowmode in {channel_mention} is {minutes} minute{minute_suffix} and {seconds} second{second_suffix}."

    @staticmethod
    async def _get_slowmode(
        ctx: commands.Context[Tux],
        channel: SlowmodeChannel,
    ) -> None:
        """
        Display the current slowmode setting for a channel.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context
        channel : SlowmodeChannel
            The channel to check
        """
        try:
            # Check if this channel has a slowmode_delay attribute
            if not hasattr(channel, "slowmode_delay"):
                await Slowmode._send_response(
                    ctx,
                    "This channel type doesn't support slowmode.",
                )
                return

            delay = channel.slowmode_delay
            message = Slowmode._format_slowmode_message(delay, channel.mention)
            await Slowmode._send_response(ctx, message)
        except Exception as error:
            logger.error(f"Failed to get slowmode: {error}")
            await Slowmode._send_response(ctx, f"Failed to get slowmode: {error}")

    async def _set_slowmode(
        self,
        ctx: commands.Context[Tux],
        channel: SlowmodeChannel,
        delay: str,
    ) -> None:
        """
        Set the slowmode delay for a channel.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context
        channel : SlowmodeChannel
            The channel to modify
        delay : str
            The delay string to parse
        """
        # Verify this channel supports slowmode
        if not self._channel_supports_slowmode(channel):
            await Slowmode._send_response(
                ctx,
                "This channel type doesn't support slowmode.",
            )
            return

        delay_seconds = self._parse_delay(delay)

        if delay_seconds is None:
            await Slowmode._send_response(
                ctx,
                "Invalid delay format. Examples: `5`, `5s`, `2m`",
            )
            return

        max_slowmode = 21600  # 6 hours, Discord's maximum
        if not (0 <= delay_seconds <= max_slowmode):
            await Slowmode._send_response(
                ctx,
                f"Slowmode delay must be between 0 and {max_slowmode} seconds (6 hours).",
            )
            return

        try:
            await channel.edit(slowmode_delay=delay_seconds)
            if delay_seconds == 0:
                message = f"Slowmode has been disabled in {channel.mention}."
            else:
                prefix = "Slowmode set to"
                message = f"{prefix} {self._format_slowmode_message(delay_seconds, channel.mention).split('is')[1].strip()}"
            await Slowmode._send_response(ctx, message)
            logger.info(f"{ctx.author} set slowmode to {delay_seconds}s in {channel}")

        except discord.Forbidden:
            await Slowmode._send_response(
                ctx,
                f"I don't have permission to change slowmode in {channel.mention}.",
            )

        except discord.HTTPException as error:
            await Slowmode._send_response(ctx, f"Failed to set slowmode: {error}")
            logger.error(f"Failed to set slowmode: {error}")

    @staticmethod
    def _parse_delay(delay: str) -> int | None:
        """
        Parse a delay string into seconds.

        Parameters
        ----------
        delay : str
            The delay string to parse (e.g., "5", "5s", "2m")

        Returns
        -------
        Optional[int]
            The delay in seconds, or None if invalid format
        """
        try:
            # Handle suffix formats
            delay = delay.lower().strip()

            if delay.endswith("s"):
                return int(delay[:-1])
            if delay.endswith("m"):
                return int(delay[:-1]) * 60
            if delay.endswith("h"):
                # sourcery skip: assign-if-exp, reintroduce-else
                return int(delay[:-1]) * 3600
            return int(delay)
        except ValueError as e:
            logger.debug(f"Invalid delay format '{delay}': {e}")
            return None


async def setup(bot: Tux) -> None:
    """Set up the Slowmode cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Slowmode(bot))
