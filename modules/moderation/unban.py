from contextlib import suppress

import discord
from bot import Tux
from discord.ext import commands
from utils import checks
from utils.constants import CONST
from utils.flags import UnbanFlags
from utils.functions import generate_usage

from prisma.enums import CaseType

from . import ModerationCogBase


class Unban(ModerationCogBase):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.unban.usage = generate_usage(self.unban, UnbanFlags)

    async def resolve_user_from_ban_list(self, ctx: commands.Context[Tux], identifier: str) -> discord.User | None:
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
        matches = [user for user in banned_users if identifier_lower in user.name.lower()]

        return matches[0] if len(matches) == 1 else None

    # New private method extracted from the nested function
    async def _perform_unban(
        self,
        ctx: commands.Context[Tux],
        user: discord.User,
        final_reason: str,
        guild: discord.Guild,  # Pass guild explicitly
    ) -> None:
        """Executes the core unban action and case creation."""
        # We already checked that user is not None in the main command
        assert user is not None, "User cannot be None at this point"
        await self.execute_mod_action(
            ctx=ctx,
            case_type=CaseType.UNBAN,
            user=user,
            reason=final_reason,
            silent=True,  # No DM for unbans due to user not being in the guild
            dm_action="",  # No DM for unbans
            actions=[(guild.unban(user, reason=final_reason), type(None))],  # Use passed guild
        )

    @commands.hybrid_command(
        name="unban",
        aliases=["ub"],
    )
    @commands.guild_only()
    @checks.has_pl(3)
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

        Raises
        ------
        discord.Forbidden
            If the bot does not have the necessary permissions.
        discord.HTTPException
            If an error occurs while unbanning the user.
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
                await self.send_error_response(
                    ctx,
                    f"Could not find '{username_or_id}' in the ban list. Try using the exact username or ID.",
                )
                return

        # Check if the user is banned
        try:
            await ctx.guild.fetch_ban(user)
        except discord.NotFound:
            await self.send_error_response(ctx, f"{user} is not banned.")
            return

        # Check if moderator has permission to unban the user
        if not await self.check_conditions(ctx, user, ctx.author, "unban"):
            return

        final_reason = reason or CONST.DEFAULT_REASON
        guild = ctx.guild

        try:
            # Call the lock executor with a lambda referencing the new private method
            await self.execute_user_action_with_lock(
                user.id,
                lambda: self._perform_unban(ctx, user, final_reason, guild),
            )
        except discord.NotFound:
            # This might occur if the user was unbanned between the fetch_ban check and the lock acquisition
            await self.send_error_response(ctx, f"{user} is no longer banned.")
        except discord.HTTPException as e:
            # Catch potential errors during the unban action forwarded by execute_mod_action
            await self.send_error_response(ctx, f"Failed to unban {user}", e)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Unban(bot))
