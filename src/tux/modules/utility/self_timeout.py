"""
Self-timeout functionality for Discord users.

This module allows users to voluntarily timeout themselves for specified
durations with confirmation dialogs and automatic AFK status management.
"""

from datetime import UTC, datetime, timedelta

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.modules.utility import add_afk, del_afk
from tux.shared.functions import convert_to_seconds, seconds_to_human_readable
from tux.ui.views.confirmation import ConfirmationDanger


class SelfTimeout(BaseCog):
    """Discord cog for self-timeout functionality."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the SelfTimeout cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    async def _send_error_message(
        self,
        ctx: commands.Context[Tux],
        message: str,
    ) -> None:
        """Send an error message, handling both slash and prefix commands.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        message : str
            The error message to send.
        """
        if ctx.interaction:
            await ctx.interaction.followup.send(message, ephemeral=True)
        else:
            await ctx.reply(message, ephemeral=True)

    def _validate_duration(
        self,
        duration_seconds: int,
        duration_str: str,
        user_id: int,
    ) -> str | None:
        """Validate timeout duration and return error message if invalid.

        Parameters
        ----------
        duration_seconds : int
            The duration in seconds.
        duration_str : str
            The original duration string for logging.
        user_id : int
            The user ID for logging.

        Returns
        -------
        str | None
            Error message if invalid, None if valid.
        """
        if duration_seconds == 0:
            logger.debug(
                f"Invalid timeout duration format: {duration_str} (user: {user_id})",
            )
            return "Error! Invalid time format"

        if duration_seconds > 604800:
            logger.debug(
                f"Timeout duration too long: {duration_seconds}s (user: {user_id})",
            )
            return "Error! duration cannot be longer than 7 days!"

        if duration_seconds < 300:
            logger.debug(
                f"Timeout duration too short: {duration_seconds}s (user: {user_id})",
            )
            return "Error! duration cannot be less than 5 minutes!"

        return None

    async def _send_confirmation_dialog(
        self,
        ctx: commands.Context[Tux],
        message_content: str,
    ) -> bool:
        """Send confirmation dialog and wait for user response.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        message_content : str
            The confirmation message content.

        Returns
        -------
        bool
            True if confirmed, False otherwise.
        """
        view = ConfirmationDanger(user=ctx.author.id)
        if ctx.interaction:
            confirmation_message = await ctx.interaction.followup.send(
                message_content,
                view=view,
                ephemeral=True,
                wait=True,
            )
        else:
            confirmation_message = await ctx.reply(
                message_content,
                view=view,
                ephemeral=True,
            )
        await view.wait()
        try:
            await confirmation_message.delete()
        except (discord.NotFound, discord.Forbidden) as e:
            # Message already deleted or bot lacks permission to delete
            logger.debug(f"Could not delete confirmation message: {e}")
        return view.value or False

    async def _send_timeout_confirmation_dm(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        duration_readable: str,
        reason: str,
    ) -> None:
        """Send DM confirmation or fallback message.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The command context.
        member : discord.Member
            The member being timed out.
        duration_readable : str
            Human-readable duration string.
        reason : str
            The timeout reason.
        """
        if ctx.guild is None:
            return
        try:
            await ctx.author.send(
                f'You have timed yourself out in guild {ctx.guild.name} for {duration_readable} with the reason "{reason}".',
            )
            logger.debug(
                f"DM sent to {member.display_name} ({member.id}) for self-timeout confirmation",
            )
        except discord.Forbidden:
            logger.debug(
                f"Failed to DM {member.display_name} ({member.id}), DMs disabled or bot blocked",
            )
            fallback_message = f'You have timed yourself out for {duration_readable} with the reason "{reason}".'
            if ctx.interaction:
                await ctx.interaction.followup.send(
                    fallback_message,
                    ephemeral=True,
                )
            else:
                await ctx.reply(fallback_message)

    async def _apply_timeout(
        self,
        member: discord.Member,
        duration_seconds: int,
        reason: str,
        guild_name: str,
        duration_readable: str,
    ) -> None:
        """Apply the timeout and set AFK status.

        Parameters
        ----------
        member : discord.Member
            The member to timeout.
        duration_seconds : int
            Duration in seconds.
        reason : str
            The timeout reason.
        guild_name : str
            The guild name for logging.
        duration_readable : str
            Human-readable duration string.
        """
        await member.timeout(
            timedelta(seconds=float(duration_seconds)),
            reason="self time-out",
        )
        logger.info(
            f"✅ Self-timeout applied: {member.display_name} ({member.id}) in {guild_name} for {duration_readable}",
        )

        timeout_until = datetime.now(UTC) + timedelta(seconds=duration_seconds)
        assert member.guild is not None
        await add_afk(
            self.db,
            reason,
            member,
            member.guild.id,
            True,
            timeout_until,
            True,
        )
        logger.debug(
            f"AFK status set for {member.id} until {timeout_until}",
        )

    @commands.hybrid_command(
        name="self_timeout",
        aliases=["sto", "stimeout", "selftimeout"],
    )
    @commands.guild_only()
    async def self_timeout(
        self,
        ctx: commands.Context[Tux],
        duration: str,
        *,
        reason: str = "No Reason.",
    ) -> None:
        """
        Time yourself out for a set duration.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command
        duration : str
            How long the timeout should last for
        reason : str [optional]
            The reason why you are timing yourself out
        """
        if ctx.guild is None:
            if ctx.interaction:
                await ctx.interaction.response.send_message(
                    "Command must be run in a guild!",
                    ephemeral=True,
                )
            else:
                await ctx.send("Command must be run in a guild!", ephemeral=True)
            return

        # Defer early to acknowledge interaction before async work
        await ctx.defer(ephemeral=True)

        member = ctx.guild.get_member(ctx.author.id)
        if member is None:
            logger.warning(
                f"Member {ctx.author.id} not found in guild {ctx.guild.id} for self-timeout",
            )
            return

        duration_seconds: int = convert_to_seconds(duration)
        duration_readable = seconds_to_human_readable(duration_seconds)

        # Validate duration
        if error_message := self._validate_duration(
            duration_seconds,
            duration,
            ctx.author.id,
        ):
            await self._send_error_message(ctx, error_message)
            return

        entry = await self.db.afk.get_afk_member(member.id, guild_id=ctx.guild.id)

        if entry is not None and reason == "No Reason.":
            # If the member is already afk and hasn't provided a reason with this command,
            # assume they want to upgrade their current AFK to a self-timeout and carry the old reason
            reason = entry.reason
            logger.debug(
                f"User {member.id} upgrading AFK to self-timeout, carrying over reason: {reason}",
            )

        logger.info(
            f"User {member.display_name} ({member.id}) requested self-timeout for {duration_readable} in guild {ctx.guild.name}",
        )

        message_content = (
            f'### WARNING\n### You are about to be timed out in the guild "{ctx.guild.name}" '
            f'for {duration} with the reason "{reason}".\n'
            "as soon as you confirm this, **you cannot cancel it or remove it early**. "
            "There is *no* provision for it to be removed by server staff on request. "
            "please think very carefully and make sure you've entered the correct values "
            "before you proceed with this command."
        )

        confirmed = await self._send_confirmation_dialog(ctx, message_content)

        if not confirmed:
            return

        logger.info(
            f"Self-timeout confirmed by {member.display_name} ({member.id}) for {duration_readable}",
        )

        await self._send_timeout_confirmation_dm(
            ctx,
            member,
            duration_readable,
            reason,
        )

        if entry is not None:
            logger.debug(
                f"Removing existing AFK status for {member.id} before self-timeout",
            )
            await del_afk(self.db, member, entry.nickname)

        await self._apply_timeout(
            member,
            duration_seconds,
            reason,
            ctx.guild.name,
            duration_readable,
        )


async def setup(bot: Tux) -> None:
    """Set up the SelfTimeout cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(SelfTimeout(bot))
