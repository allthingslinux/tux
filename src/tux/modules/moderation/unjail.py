"""
User unjailing commands for Discord moderation.

This module provides functionality to remove jail status from users,
restoring their roles and permissions in Discord servers.
"""

import asyncio

import discord
from discord.ext import commands
from loguru import logger

from tux.cache import JailStatusCache
from tux.core.bot import Tux
from tux.core.checks import requires_command_permission
from tux.core.flags import UnjailFlags
from tux.database.models import Case
from tux.database.models import CaseType as DBCaseType

from . import ModerationCogBase


class Unjail(ModerationCogBase):
    """Discord cog for removing jail status from users."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the Unjail cog.

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

    async def get_latest_jail_case(self, guild_id: int, user_id: int) -> Case | None:
        """
        Get the latest jail case for a user.

        Parameters
        ----------
        guild_id : int
            The ID of the guild to check in.
        user_id : int
            The ID of the user to check.

        Returns
        -------
        Case | None
            The latest JAIL case, or None if not found.
        """
        return await self.db.case.get_latest_jail_case(
            user_id=user_id,
            guild_id=guild_id,
        )

    async def restore_roles(
        self,
        member: discord.Member,
        role_ids: list[int],
        reason: str,
    ) -> tuple[bool, list[discord.Role]]:
        """
        Restore roles to a member with error handling.

        Parameters
        ----------
        member : discord.Member
            The member to restore roles to.
        role_ids : List[int]
            The IDs of the roles to restore.
        reason : str
            The reason for restoring the roles.

        Returns
        -------
        Tuple[bool, List[discord.Role]]
            A tuple containing whether the operation was successful and which roles were restored.
        """
        if not role_ids:
            return True, []

        # Filter out roles that no longer exist or can't be assigned
        guild = member.guild
        roles_to_add: list[discord.Role] = []
        skipped_roles: list[int] = []

        for role_id in role_ids:
            role = guild.get_role(role_id)
            if role and role.is_assignable():
                roles_to_add.append(role)
            else:
                skipped_roles.append(role_id)

        if skipped_roles:
            logger.warning(
                f"Skipping {len(skipped_roles)} roles that don't exist or can't be assigned: {skipped_roles}",
            )

        if not roles_to_add:
            return True, []

        # Try to add all roles at once
        try:
            await member.add_roles(*roles_to_add, reason=reason)

        except discord.Forbidden:
            logger.error(f"No permission to add roles to {member}")
            return False, []

        except discord.HTTPException as e:
            # If bulk add fails, try one by one
            logger.warning(f"Bulk role add failed for {member}, trying one by one: {e}")
            successful_roles: list[discord.Role] = []

            for role in roles_to_add:
                try:
                    await member.add_roles(role, reason=reason)
                    successful_roles.append(role)

                except Exception as role_e:
                    logger.error(f"Failed to add role {role} to {member}: {role_e}")

            return bool(successful_roles), successful_roles

        else:
            return True, roles_to_add

    @commands.hybrid_command(
        name="unjail",
        aliases=["uj"],
    )
    @commands.guild_only()
    @requires_command_permission()
    async def unjail(
        self,
        ctx: commands.Context[Tux],
        member: discord.Member,
        *,
        flags: UnjailFlags,
    ) -> None:
        """
        Remove a member from jail.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context in which the command is being invoked.
        member : discord.Member
            The member to unjail.
        flags : UnjailFlags
            The flags for the command. (reason: str, silent: bool)
        """
        assert ctx.guild

        # Parallelize independent database queries
        jail_role_id_task = self.db.guild_config.get_jail_role_id(ctx.guild.id)
        is_jailed_task = self.is_jailed(ctx.guild.id, member.id)
        latest_jail_case_task = self.get_latest_jail_case(ctx.guild.id, member.id)

        # Wait for all queries to complete
        jail_role_id, is_jailed_result, case = await asyncio.gather(
            jail_role_id_task,
            is_jailed_task,
            latest_jail_case_task,
        )

        # Get Discord role object (synchronous lookup)
        jail_role = None if jail_role_id is None else ctx.guild.get_role(jail_role_id)
        if not jail_role:
            await self._respond(ctx, "No jail role found.")
            return

        # Check if user is jailed
        if not is_jailed_result:
            await self._respond(ctx, "User is not jailed.")
            return

        if not case:
            await self._respond(ctx, "No jail case found.")
            return

        # Permission checks are handled by the @requires_command_permission() decorator
        # Additional validation will be handled by the ModerationCoordinator service

        # Use lock to prevent race conditions
        async def perform_unjail() -> None:
            """Perform the unjail operation with proper error handling."""
            nonlocal ctx, member, jail_role, flags, case

            # Assert case is not None for type checker (already checked above)
            assert case is not None, "Case should not be None at this point"

            # Remove jail role from member
            assert jail_role is not None, "Jail role should not be None at this point"
            await member.remove_roles(jail_role, reason=flags.reason)
            logger.info(f"Removed jail role from {member} by {ctx.author}")

            # Use moderation service for case creation, DM sending, and response
            await self.moderate_user(
                ctx=ctx,
                case_type=DBCaseType.UNJAIL,
                user=member,
                reason=flags.reason,
                silent=flags.silent,
                dm_action="removed from jail",
                actions=[],  # No additional Discord actions needed for unjail
                duration=None,
            )

            # Add roles back to member after sending the response
            if case.case_user_roles:
                success, restored_roles = await self.restore_roles(
                    member,
                    case.case_user_roles,
                    flags.reason,
                )
                if success and restored_roles:
                    logger.info(f"Restored {len(restored_roles)} roles to {member}")
                    # Note: Discord API is eventually consistent, so we don't verify roles
                    # immediately. If verification is needed, it should be done in a background
                    # task with a delay, not blocking the command response.

                elif not restored_roles:
                    logger.warning(
                        f"No roles to restore for {member} or restore action failed partially/completely.",
                    )

            # Invalidate jail status cache after unjailing
            assert ctx.guild is not None
            await JailStatusCache().invalidate(ctx.guild.id, member.id)

        # Execute the action (removed lock since moderation service handles concurrency)
        await perform_unjail()


async def setup(bot: Tux) -> None:
    """Set up the Unjail cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(Unjail(bot))
