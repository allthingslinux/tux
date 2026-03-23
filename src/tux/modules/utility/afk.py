"""
Away From Keyboard (AFK) status management.

This module provides comprehensive AFK functionality including automatic
status setting, message notifications, and nickname management for Discord users.
"""

import contextlib
import textwrap
from datetime import UTC, datetime, timedelta
from typing import cast

import discord
from discord.ext import commands, tasks
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.database.models import AFK as AFKMODEL
from tux.modules.utility import add_afk, del_afk
from tux.shared.config import CONFIG
from tux.shared.constants import (
    AFK_ALLOWED_MENTIONS,
    AFK_REASON_MAX_LENGTH,
    AFK_SLEEPING_EMOJI,
    TRUNCATION_SUFFIX,
)


class Afk(BaseCog):
    """Discord cog for managing AFK status functionality."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the AFK cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)
        logger.info("Initializing AFK cog and starting expiration handler")
        self.handle_afk_expiration.start()
        logger.debug("AFK expiration handler start() called")

    async def cog_unload(self) -> None:
        """Cancel the background task when the cog is unloaded."""
        self.handle_afk_expiration.cancel()

    @commands.Cog.listener("on_member_update")
    async def on_timeout_expire(
        self,
        before: discord.Member,
        after: discord.Member,
    ) -> None:
        """
        Handle timeout expiration for enforced AFK (self-timeout).

        When a member's timeout expires, immediately restore their nickname
        and remove their AFK status if it was an enforced self-timeout.

        Parameters
        ----------
        before : discord.Member
            The member state before the update.
        after : discord.Member
            The member state after the update.
        """
        # Check if timeout was removed (expired or manually removed)
        if before.timed_out_until is not None and after.timed_out_until is None:
            logger.debug(
                f"Timeout removed for {after.name} ({after.id}), checking for enforced AFK",
            )
            # Check if member has an enforced AFK entry
            entry = await self._get_afk_entry(after.id, after.guild.id)
            if entry and entry.enforced:
                logger.info(
                    f"Timeout expired for {after.name} ({after.id}), removing enforced AFK status via on_member_update",
                )
                # Restore nickname and remove AFK entry
                # This happens before the expiration handler runs, preventing double-processing
                await del_afk(self.db, after, entry.nickname)
            elif entry:
                logger.debug(
                    f"Member {after.id} has AFK entry but not enforced (enforced={entry.enforced})",
                )
            else:
                logger.debug(f"No AFK entry found for {after.id}")

    @commands.hybrid_command(name="afk")
    @commands.guild_only()
    async def afk(
        self,
        ctx: commands.Context[Tux],
        *,
        reason: str = "No reason.",
    ) -> None:
        """
        Set yourself as AFK.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        reason : str, optional
            The reason you are AFK.
        """
        target = ctx.author

        assert ctx.guild
        assert isinstance(target, discord.Member)

        # Defer early to acknowledge interaction before async work
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        # Check if user is already AFK to prevent duplication
        entry = await self._get_afk_entry(target.id, ctx.guild.id)

        if entry is not None:
            # Self-timed out (enforced): they must use /clearafk, not overwrite with regular AFK
            if entry.enforced:
                logger.debug(
                    f"User {target.id} tried $afk while self-timed out in guild {ctx.guild.id}",
                )
                await self._send_afk_response(
                    ctx,
                    f"{AFK_SLEEPING_EMOJI} || You're currently self-timed out. "
                    "Use `/clearafk` (or ask staff) to clear that first.",
                )
                return
            logger.debug(f"User {target.id} already AFK in guild {ctx.guild.id}")
            await self._send_afk_response(
                ctx,
                f"{AFK_SLEEPING_EMOJI} || You are already AFK! Reason: `{entry.reason}`",
            )
            return

        shortened_reason = textwrap.shorten(
            reason,
            width=AFK_REASON_MAX_LENGTH,
            placeholder=TRUNCATION_SUFFIX,
        )

        await add_afk(self.db, shortened_reason, target, ctx.guild.id, False)
        logger.info(
            f"AFK status set: {target.name} ({target.id}) in {ctx.guild.name} - Reason: {shortened_reason}",
        )

        await self._send_afk_response(
            ctx,
            f"{AFK_SLEEPING_EMOJI} || You are now afk! Reason: `{shortened_reason}`",
        )

    @commands.hybrid_command(name="permafk")
    @commands.guild_only()
    async def permafk(
        self,
        ctx: commands.Context[Tux],
        *,
        reason: str = "No reason.",
    ) -> None:
        """
        Set yourself permanently AFK until you rerun the command.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        reason : str, optional
            The reason you are AFK.
        """
        target = ctx.author
        assert ctx.guild
        assert isinstance(target, discord.Member)

        # Defer early to acknowledge interaction before async work
        if ctx.interaction:
            await ctx.defer(ephemeral=True)

        entry = await self._get_afk_entry(target.id, ctx.guild.id)
        if entry is not None:
            # Self-timed out (enforced): del_afk would remove DB entry but not Discord timeout
            if entry.enforced:
                logger.debug(
                    f"User {target.id} tried $permafk while self-timed out in guild {ctx.guild.id}",
                )
                await self._send_afk_response(
                    ctx,
                    f"{AFK_SLEEPING_EMOJI} || You're currently self-timed out. "
                    "Use `/clearafk` (or ask staff) to clear that first.",
                )
                return
            await del_afk(self.db, target, entry.nickname)
            logger.info(
                f"Permanent AFK toggled off: {target.name} ({target.id}) in {ctx.guild.name}",
            )
            await self._send_afk_response(ctx, "Welcome back!")
            return

        shortened_reason = textwrap.shorten(
            reason,
            width=AFK_REASON_MAX_LENGTH,
            placeholder=TRUNCATION_SUFFIX,
        )
        await add_afk(self.db, shortened_reason, target, ctx.guild.id, True)
        logger.info(
            f"💤 Permanent AFK set: {target.name} ({target.id}) in {ctx.guild.name} - Reason: {shortened_reason}",
        )

        await self._send_afk_response(
            ctx,
            f"{AFK_SLEEPING_EMOJI} || You are now permanently afk! To remove afk run this command again. Reason: `{shortened_reason}`",
        )

    async def _send_afk_response(
        self,
        ctx: commands.Context[Tux],
        content: str,
    ) -> None:
        """Send a response for AFK commands with consistent formatting."""
        if ctx.interaction:
            await ctx.interaction.followup.send(
                content=content,
                allowed_mentions=AFK_ALLOWED_MENTIONS,
                ephemeral=True,
            )
        else:
            await ctx.reply(
                content=content,
                allowed_mentions=AFK_ALLOWED_MENTIONS,
            )

    async def _get_afk_entry(self, member_id: int, guild_id: int) -> AFKMODEL | None:
        """
        Get an AFK entry for a member in a guild.

        Returns
        -------
        AFKMODEL | None
            The AFK entry if found, None otherwise.
        """
        return await self.db.afk.get_afk_member(member_id, guild_id)

    @commands.Cog.listener("on_message")
    async def remove_afk(self, message: discord.Message) -> None:
        """
        Remove the AFK status of a member when they send a message.

        Parameters
        ----------
        message : discord.Message
            The message to check.
        """
        try:
            # Skip AFK processing during maintenance mode
            if (
                getattr(self.bot, "maintenance_mode", False)
                or self.bot.maintenance_mode
            ):
                return

            if not message.guild or message.author.bot:
                return

            assert isinstance(message.author, discord.Member)

            entry = await self._get_afk_entry(message.author.id, message.guild.id)

            if not entry:
                return

            if entry.since + timedelta(seconds=10) > datetime.now(UTC).replace(
                tzinfo=None,
            ):
                return

            if await self.db.afk.is_perm_afk(
                message.author.id,
                guild_id=message.guild.id,
            ):
                return

            # Restore nickname first before removing from database
            # This ensures if nickname restore fails, AFK entry still exists
            nickname_restored = False
            with contextlib.suppress(discord.Forbidden):
                await message.author.edit(nick=entry.nickname)
                nickname_restored = True
                logger.debug(
                    f"Nickname restored for {message.author.id}: {entry.nickname}",
                )

            # Only remove from database after nickname is restored (or attempted)
            # Re-check entry exists to avoid race condition with expiration handler
            current_entry = await self._get_afk_entry(
                message.author.id,
                message.guild.id,
            )
            if current_entry is not None:
                await self.db.afk.remove_afk(message.author.id, message.guild.id)
                logger.info(
                    f"✅ AFK status removed: {message.author.name} ({message.author.id}) returned to {message.guild.name}",
                )
                await message.reply("Welcome back!", delete_after=5)
            # Entry was already removed (likely by expiration handler)
            # If nickname wasn't restored, try to restore it now
            elif not nickname_restored:
                with contextlib.suppress(discord.Forbidden):
                    await message.author.edit(nick=entry.nickname)
                    logger.debug(
                        f"Nickname restored for {message.author.id} after race condition: {entry.nickname}",
                    )
        except Exception as e:
            logger.exception(
                f"Error in remove_afk listener for message {message.id}: {e}",
            )

    @commands.Cog.listener("on_message")
    async def check_afk(self, message: discord.Message) -> None:
        """
        Check if a message mentions an AFK member.

        Parameters
        ----------
        message : discord.Message
            The message to check.
        """
        try:
            if not message.guild or message.author.bot:
                return

            # Check if the message is a self-timeout command (prefix or slash).
            # if it is, the member is probably trying to upgrade to a self-timeout, so AFK status should not be removed.
            prefix = (
                await self.bot.prefix_manager.get_prefix(message.guild.id)
                if self.bot.prefix_manager
                else CONFIG.get_prefix()
            )
            # Check for prefix commands
            if message.content.startswith(f"{prefix}sto"):
                return
            # Check for slash command invocations (interaction_metadata only; message.interaction is deprecated)
            command_name: str | None = (
                getattr(message.interaction_metadata, "name", None)
                if message.interaction_metadata
                else None
            )
            if command_name and command_name in (
                "self_timeout",
                "sto",
                "stimeout",
                "selftimeout",
            ):
                logger.debug(
                    "Ignoring self_timeout command response from %s",
                    message.author.id,
                )
                return

            afks_mentioned: list[tuple[discord.Member, AFKMODEL]] = []

            for mentioned in message.mentions:
                entry = await self._get_afk_entry(mentioned.id, message.guild.id)
                if entry:
                    # Check if entry has expired
                    if entry.until is not None:
                        until_naive = (
                            entry.until.replace(tzinfo=None)
                            if entry.until.tzinfo
                            else entry.until
                        )
                        now_naive = datetime.now(UTC).replace(tzinfo=None)
                        if until_naive < now_naive:
                            # Entry has expired - clean it up immediately
                            logger.info(
                                f"Cleaning up expired AFK entry for {mentioned.name} ({mentioned.id}) on mention",
                            )
                            await del_afk(
                                self.db,
                                cast(discord.Member, mentioned),
                                entry.nickname,
                            )
                            continue
                    afks_mentioned.append((cast(discord.Member, mentioned), entry))

            if not afks_mentioned:
                return

            logger.debug(
                f"AFK notification: {len(afks_mentioned)} AFK users mentioned in {message.guild.name}",
            )

            msgs: list[str] = []
            for mentioned, afk in afks_mentioned:
                # Database stores naive UTC datetimes, convert to aware for timestamp calculation
                # All database datetimes are stored as naive UTC
                since = (
                    afk.since.replace(tzinfo=UTC)
                    if afk.since.tzinfo is None
                    else afk.since
                )
                until_str = ""
                if afk.until is not None:
                    until = (
                        afk.until.replace(tzinfo=UTC)
                        if afk.until.tzinfo is None
                        else afk.until
                    )
                    until_str = f"until <t:{int(until.timestamp())}:f>"
                msgs.append(
                    f'{mentioned.mention} is currently AFK {until_str}: "{afk.reason}" [<t:{int(since.timestamp())}:R>]',
                )

            await message.reply(
                content="\n".join(msgs),
                allowed_mentions=AFK_ALLOWED_MENTIONS,
            )
        except Exception as e:
            logger.exception(
                f"Error in check_afk listener for message {message.id}: {e}",
            )

    @tasks.loop(seconds=60, name="afk_expiration_handler")
    async def handle_afk_expiration(self) -> None:
        """Check AFK database at a regular interval, remove AFK from users with an entry that has expired."""
        # Skip AFK expiration processing during maintenance mode
        if self.bot.maintenance_mode:
            return

        for guild in self.bot.guilds:
            expired_entries = await self._get_expired_afk_entries(guild.id)

            if expired_entries:
                logger.info(
                    f"Processing {len(expired_entries)} expired AFK entries in {guild.name}",
                )

            for entry in expired_entries:
                # Re-check if entry still exists (could have been removed by user message)
                current_entry = await self._get_afk_entry(entry.member_id, guild.id)
                if current_entry is None:
                    # Entry was already removed, skip
                    logger.debug(
                        f"AFK entry for {entry.member_id} already removed in {guild.name}",
                    )
                    continue

                member = guild.get_member(entry.member_id)

                if member is None:
                    # Handles the edge case of a user leaving the guild while still temp-AFK
                    logger.debug(
                        f"Removing AFK for departed member {entry.member_id} from {guild.name}",
                    )
                    await self.db.afk.remove_afk(entry.member_id, guild.id)
                else:
                    logger.debug(
                        f"Expiring AFK status for {member.name} ({member.id}) in {guild.name}",
                    )
                    # Note: Discord timeout is automatically removed by Discord when it expires
                    # The on_member_update listener handles immediate cleanup when timeout is removed
                    # This handler is a safety net for entries that weren't caught by the listener
                    # Use current_entry to ensure we have the latest nickname
                    await del_afk(self.db, member, current_entry.nickname)

    @handle_afk_expiration.before_loop
    async def before_handle_afk_expiration(self) -> None:
        """Wait until the bot is ready."""
        await self.bot.wait_until_ready()
        logger.info("AFK expiration handler started (runs every 60 seconds)")

    @handle_afk_expiration.error
    async def on_handle_afk_expiration_error(self, error: BaseException) -> None:
        """Handle errors in the AFK expiration handler loop."""
        logger.error(f"Error in AFK expiration handler loop: {error}")
        if isinstance(error, Exception):
            self.bot.sentry_manager.capture_exception(error)
        else:
            raise error

    async def _get_expired_afk_entries(self, guild_id: int) -> list[AFKMODEL]:
        """
        Get all expired AFK entries for a guild.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check.

        Returns
        -------
        list[AFKMODEL]
            A list of expired AFK entries.
        """
        return await self.db.afk.get_expired_afk_members(guild_id)


async def setup(bot: Tux) -> None:
    """Set up the Afk cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Afk(bot))
