"""
Away From Keyboard (AFK) status management.

This module provides comprehensive AFK functionality including automatic
status setting, message notifications, and nickname management for Discord users.
"""

import contextlib
import textwrap
from datetime import datetime, timedelta
from typing import cast
from zoneinfo import ZoneInfo

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
        self.handle_afk_expiration.start()

    async def cog_unload(self) -> None:
        """Cancel the background task when the cog is unloaded."""
        self.handle_afk_expiration.cancel()

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

        # Check if user is already AFK to prevent duplication
        entry = await self._get_afk_entry(target.id, ctx.guild.id)

        if entry is not None:
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

        entry = await self._get_afk_entry(target.id, ctx.guild.id)
        if entry is not None:
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
        await ctx.reply(
            content=content,
            allowed_mentions=AFK_ALLOWED_MENTIONS,
            ephemeral=True,
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
        if not message.guild or message.author.bot:
            return

        assert isinstance(message.author, discord.Member)

        entry = await self._get_afk_entry(message.author.id, message.guild.id)

        if not entry:
            return

        if entry.since + timedelta(seconds=10) > datetime.now(ZoneInfo("UTC")):
            return

        if await self.db.afk.is_perm_afk(message.author.id, guild_id=message.guild.id):
            return

        await self.db.afk.remove_afk(message.author.id, message.guild.id)
        logger.info(
            f"✅ AFK status removed: {message.author.name} ({message.author.id}) returned to {message.guild.name}",
        )

        await message.reply("Welcome back!", delete_after=5)

        # Suppress Forbidden errors if the bot doesn't have permission to change the nickname
        with contextlib.suppress(discord.Forbidden):
            await message.author.edit(nick=entry.nickname)
            logger.debug(f"Nickname restored for {message.author.id}: {entry.nickname}")

    @commands.Cog.listener("on_message")
    async def check_afk(self, message: discord.Message) -> None:
        """
        Check if a message mentions an AFK member.

        Parameters
        ----------
        message : discord.Message
            The message to check.
        """
        if not message.guild or message.author.bot:
            return

        # Check if the message is a self-timeout command.
        # if it is, the member is probably trying to upgrade to a self-timeout, so AFK status should not be removed.
        prefix = (
            await self.bot.prefix_manager.get_prefix(message.guild.id)
            if self.bot.prefix_manager
            else CONFIG.get_prefix()
        )
        if message.content.startswith(f"{prefix}sto"):
            return

        afks_mentioned: list[tuple[discord.Member, AFKMODEL]] = []

        for mentioned in message.mentions:
            entry = await self._get_afk_entry(mentioned.id, message.guild.id)
            if entry:
                afks_mentioned.append((cast(discord.Member, mentioned), entry))

        if not afks_mentioned:
            return

        logger.debug(
            f"AFK notification: {len(afks_mentioned)} AFK users mentioned in {message.guild.name}",
        )

        msgs: list[str] = [
            f'{mentioned.mention} is currently AFK {f"until <t:{int(afk.until.timestamp())}:f>" if afk.until is not None else ""}: "{afk.reason}" [<t:{int(afk.since.timestamp())}:R>]'
            for mentioned, afk in afks_mentioned
        ]

        await message.reply(
            content="\n".join(msgs),
            allowed_mentions=AFK_ALLOWED_MENTIONS,
        )

    @tasks.loop(seconds=120, name="afk_expiration_handler")
    async def handle_afk_expiration(self) -> None:
        """Check AFK database at a regular interval, remove AFK from users with an entry that has expired."""
        for guild in self.bot.guilds:
            expired_entries = await self._get_expired_afk_entries(guild.id)

            if expired_entries:
                logger.info(
                    f"Processing {len(expired_entries)} expired AFK entries in {guild.name}",
                )

            for entry in expired_entries:
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
                    await del_afk(self.db, member, entry.nickname)

    @handle_afk_expiration.before_loop
    async def before_handle_afk_expiration(self) -> None:
        """Wait until the bot is ready."""
        await self.bot.wait_until_ready()

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
