"""
Jail moderation commands.

This module provides functionality to jail Discord members by assigning them
a jail role and removing their other roles. Jailed members are typically restricted
to a designated jail channel and lose access to other server channels.

If a jailed member leaves the server and rejoins before being unjailed, they are
automatically re-jailed on rejoin (on_member_join). A delayed cleanup run strips
roles added by other on-join handlers (e.g. TTY roles, which add after 5s).
"""

import asyncio

import discord
from discord.ext import commands
from loguru import logger

from tux.cache import JailStatusCache
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

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Re-apply jail if the member was jailed and left the server before being unjailed."""
        if not member.guild:
            return
        if not await self.is_jailed(member.guild.id, member.id):
            return
        jail_role = await self.get_jail_role(member.guild)
        if not jail_role:
            logger.warning(
                f"Cannot rejail {member} on rejoin: no jail role configured for guild {member.guild.id} ({member.guild.name})",
            )
            return
        jail_channel_id = await self.db.guild_config.get_jail_channel_id(
            member.guild.id,
        )
        if not jail_channel_id:
            logger.warning(
                f"Cannot rejail {member} on rejoin: no jail channel configured for guild {member.guild.id} ({member.guild.name})",
            )
            return
        reason = "Re-jail on rejoin (was jailed before leaving)"
        try:
            await member.add_roles(jail_role, reason=reason)
            if user_roles := self._get_manageable_roles(member, jail_role):
                try:
                    await member.remove_roles(*user_roles, reason=reason)
                except Exception as e:
                    logger.warning(
                        f"Failed to remove all roles at once from {member} on rejail, falling back to individual removal: {e}",
                    )
                    for role in user_roles:
                        try:
                            await member.remove_roles(role, reason=reason)
                        except Exception as role_e:
                            logger.error(
                                f"Failed to remove role {role} from {member} on rejail: {role_e}",
                            )
        except discord.Forbidden as e:
            logger.error(
                f"Failed to rejail {member} on rejoin in guild {member.guild.id}: {e}",
            )
            return
        except Exception as e:
            logger.exception(f"Unexpected error rejailing {member} on rejoin: {e}")
            return
        logger.info(
            f"Re-jailed {member} on rejoin in guild {member.guild.id} ({member.guild.name})",
        )
        # Invalidate so next is_jailed fetches fresh from DB (consistent with jail command)
        await JailStatusCache().invalidate(member.guild.id, member.id)
        # Strip roles added by other on_member_join handlers (e.g. TTY roles ~5s)
        asyncio.create_task(  # noqa: RUF006
            self._delayed_rejail_cleanup(member.guild.id, member.id),
        )

    async def _delayed_rejail_cleanup(self, guild_id: int, user_id: int) -> None:
        """
        Run a second pass to remove roles added by delayed on-join logic.

        Plugins like TTY roles add a role 5 seconds after join. This runs
        after that window and strips any such roles if the user is still jailed.
        """
        try:
            await asyncio.sleep(6)
            guild = self.bot.get_guild(guild_id)
            if not guild:
                return
            member = guild.get_member(user_id)
            if not member or not await self.is_jailed(guild_id, user_id):
                return
            jail_role = await self.get_jail_role(guild)
            if not jail_role:
                return
            if user_roles := self._get_manageable_roles(member, jail_role):
                try:
                    await member.remove_roles(
                        *user_roles,
                        reason="Re-jail delayed cleanup (on-join roles)",
                    )
                except Exception as e:
                    logger.warning(
                        f"Delayed rejail cleanup: failed to remove roles from {member}: {e}",
                    )
                    for role in user_roles:
                        try:
                            await member.remove_roles(
                                role,
                                reason="Re-jail delayed cleanup (on-join roles)",
                            )
                        except Exception as role_e:
                            logger.error(
                                f"Delayed rejail cleanup: failed to remove {role} from {member}: {role_e}",
                            )
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception(f"Delayed rejail cleanup for {guild_id}/{user_id}: {e}")

    @commands.hybrid_command(
        name="jail",
        aliases=["j"],
    )
    @commands.guild_only()
    @commands.cooldown(1, 5.0, commands.BucketType.guild)
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

        # One DB round-trip for jail config when cache misses; is_jailed in parallel
        jail_config_task = self.db.guild_config.get_jail_config(ctx.guild.id)
        is_jailed_task = self.is_jailed(ctx.guild.id, member.id)
        (jail_role_id, jail_channel_id), is_jailed_result = await asyncio.gather(
            jail_config_task,
            is_jailed_task,
        )

        # Get Discord objects (these are synchronous lookups)
        jail_role = None if jail_role_id is None else ctx.guild.get_role(jail_role_id)
        if not jail_role:
            await self._respond(ctx, "No jail role found.")
            return

        jail_channel = (
            ctx.guild.get_channel(jail_channel_id)
            if jail_channel_id is not None
            else None
        )
        if not jail_channel or not isinstance(jail_channel, discord.TextChannel):
            await self._respond(ctx, "No jail channel found.")
            return

        # Check if user is already jailed
        if is_jailed_result:
            await self._respond(ctx, "User is already jailed.")
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

        # Invalidate jail status cache after jailing
        await JailStatusCache().invalidate(ctx.guild.id, member.id)

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
