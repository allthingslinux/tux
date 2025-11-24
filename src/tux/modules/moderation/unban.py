"""
User unbanning commands for Discord moderation.

This module provides functionality to unban users from Discord servers,
with support for resolving users from ban lists using various identifiers.
"""

from contextlib import suppress

import discord
from discord.ext import commands

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.flags import UnbanFlags
from tux.database.models import CaseType as DBCaseType
from tux.shared.constants import DEFAULT_REASON

from . import ModerationCogBase


class Unban(ModerationCogBase):
    """Discord cog for unbanning users from servers."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Unban cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    async def resolve_user_from_ban_list(
        self,
        ctx: commands.Context[Tux],
        identifier: str,
    ) -> discord.User | None:
        """
        Resolve a user from the ban list using username, ID, or partial info.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        identifier : str
            The username, ID, or partial identifier to resolve.

        Returns
        -------
        Optional[discord.User]
            The user if found, None otherwise.
        """
        assert ctx.guild

        # Get the list of banned users
        banned_users = [ban.user async for ban in ctx.guild.bans()]

        # Try ID first
        with suppress(ValueError):
            user_id = int(identifier)
            for user in banned_users:
                if user.id == user_id:
                    return user

        # Try exact username or username#discriminator matching
        for user in banned_users:
            if user.name.lower() == identifier.lower():
                return user
            if str(user).lower() == identifier.lower():
                return user

        # Try partial name matching
        identifier_lower = identifier.lower()
        matches = [
            user for user in banned_users if identifier_lower in user.name.lower()
        ]

        return matches[0] if len(matches) == 1 else None

    # New private method extracted from the nested function
    async def _perform_unban(
        self,
        ctx: commands.Context[Tux],
        user: discord.User,
        final_reason: str,
        guild: discord.Guild,
    ) -> None:
        """Execute the core unban action and case creation."""
        # We already checked that user is not None in the main command
        assert user is not None, "User cannot be None at this point"
        await self.moderate_user(
            ctx=ctx,
            case_type=DBCaseType.UNBAN,
            user=user,
            reason=final_reason,
            silent=True,  # No DM for unbans due to user not being in the guild
            dm_action="",  # No DM for unbans
            actions=[(lambda: guild.unban(user, reason=final_reason), type(None))],
        )

    @commands.hybrid_command(
        name="unban",
        aliases=["ub"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def unban(
        self,
        ctx: commands.Context[Tux],
        username_or_id: str,
        reason: str | None = None,
        *,
        flags: UnbanFlags,
    ) -> None:
        """
        Unban a user from the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.
        username_or_id : str
            The username or ID of the user to unban.
        reason : Optional[str]
            The reason for the unban.
        flags : UnbanFlags
            The flags for the command.
        """
        assert ctx.guild

        await ctx.defer(ephemeral=True)

        # First, try standard user conversion
        try:
            user = await commands.UserConverter().convert(ctx, username_or_id)
        except commands.UserNotFound:
            # If that fails, try more flexible ban list matching
            user = await self.resolve_user_from_ban_list(ctx, username_or_id)
            if not user:
                await ctx.reply(
                    f"Could not find '{username_or_id}' in the ban list. Try using the exact username or ID.",
                    mention_author=False,
                )
                return

        # Check if the user is banned
        try:
            await ctx.guild.fetch_ban(user)

        except discord.NotFound:
            await ctx.reply(f"{user} is not banned.", mention_author=False)
            return

        final_reason = reason or DEFAULT_REASON
        guild = ctx.guild

        await self._perform_unban(ctx, user, final_reason, guild)


async def setup(bot: Tux) -> None:
    """Set up the Unban cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Unban(bot))
