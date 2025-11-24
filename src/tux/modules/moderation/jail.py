"""
Jail moderation commands.

This module provides functionality to jail Discord members by assigning them
a jail role and removing their other roles. Jailed members are typically restricted
to a designated jail channel and lose access to other server channels.
"""

import discord
from discord.ext import commands
from loguru import logger

from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.flags import JailFlags
from tux.database.models import CaseType

from . import ModerationCogBase


class Jail(ModerationCogBase):
    """Discord cog for jail moderation commands.

    Provides functionality to jail Discord members by assigning them a jail role
    and removing their other manageable roles. Jailed members are restricted to
    a designated jail channel and lose access to other server channels.
    """

    def __init__(self, bot: Tux) -> None:
        """Initialize the Jail cog.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this cog to.
        """
        super().__init__(bot)

    async def get_jail_role(self, guild: discord.Guild) -> discord.Role | None:
        """
        Get the jail role for the guild.

        Parameters
        ----------
        guild : discord.Guild
            The guild to get the jail role for.

        Returns
        -------
        discord.Role | None
            The jail role, or None if not found.
        """
        jail_role_id = await self.db.guild_config.get_jail_role_id(guild.id)
        return None if jail_role_id is None else guild.get_role(jail_role_id)

    async def get_jail_channel(
        self,
        guild: discord.Guild,
    ) -> discord.TextChannel | None:
        """
        Get the jail channel for the guild.

        Returns
        -------
        discord.TextChannel | None
            The jail channel if found, None otherwise.
        """
        jail_channel_id = await self.db.guild_config.get_jail_channel_id(guild.id)
        channel = (
            guild.get_channel(jail_channel_id) if jail_channel_id is not None else None
        )
        return channel if isinstance(channel, discord.TextChannel) else None

    @commands.hybrid_command(
        name="jail",
        aliases=["j"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def jail(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: JailFlags,
    ) -> None:
        """
        Jail a member in the server.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to jail.
        flags : JailFlags
            The flags for the command. (reason: str, silent: bool)
        """
        assert ctx.guild

        await ctx.defer(ephemeral=True)

        # Get jail role
        jail_role = await self.get_jail_role(ctx.guild)
        if not jail_role:
            await ctx.send("No jail role found.", ephemeral=True)
            return

        # Get jail channel
        jail_channel = await self.get_jail_channel(ctx.guild)
        if not jail_channel:
            await ctx.send("No jail channel found.", ephemeral=True)
            return

        # Check if user is already jailed
        if await self.is_jailed(ctx.guild.id, member.id):
            await ctx.send("User is already jailed.", ephemeral=True)
            return

        # Get roles that can be managed by the bot
        user_roles = self._get_manageable_roles(member, jail_role)
        user_role_ids = [role.id for role in user_roles]

        # Add jail role immediately - this is the most important part
        # Exceptions will bubble to global error handler for proper user feedback
        await member.add_roles(jail_role, reason=flags.reason)

        # Send DM to member and handle case response using the moderation service
        # The moderation service will handle case creation, DM sending, and response
        await self.moderate_user(
            ctx=ctx,
            case_type=CaseType.JAIL,
            user=member,
            reason=flags.reason,
            silent=flags.silent,
            dm_action="jailed",
            actions=[],  # No additional Discord actions needed for jail
            duration=None,
            case_user_roles=user_role_ids,  # Store roles for unjail
        )

        # Remove old roles in the background after sending the response
        # Use graceful degradation - if some roles fail, continue with others
        if user_roles:
            try:
                # Try to remove all at once for efficiency
                await member.remove_roles(*user_roles, reason=flags.reason)
            except Exception as e:
                logger.warning(
                    f"Failed to remove all roles at once from {member}, falling back to individual removal: {e}",
                )
                # Fall back to removing one by one
                for role in user_roles:
                    try:
                        await member.remove_roles(role, reason=flags.reason)
                    except Exception as role_e:
                        logger.error(
                            f"Failed to remove role {role} from {member}: {role_e}",
                        )
                        # Continue with other roles even if one fails

    @staticmethod
    def _get_manageable_roles(
        member: discord.Member,
        jail_role: discord.Role,
    ) -> list[discord.Role]:
        """
        Get the roles that can be managed by the bot.

        Parameters
        ----------
        member : discord.Member
            The member to jail.
        jail_role : discord.Role
            The jail role.

        Returns
        -------
        list[discord.Role]
            A list of roles that can be managed by the bot.
        """
        return [
            role
            for role in member.roles
            if not (
                role.is_bot_managed()
                or role.is_premium_subscriber()
                or role.is_integration()
                or role.is_default()
                or role == jail_role
            )
            and role.is_assignable()
        ]


async def setup(bot: Tux) -> None:
    """Set up the Jail cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Jail(bot))
