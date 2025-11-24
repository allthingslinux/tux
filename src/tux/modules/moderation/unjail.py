"""
User unjailing commands for Discord moderation.

This module provides functionality to remove jail status from users,
restoring their roles and permissions in Discord servers.
"""

import asyncio

import discord
from discord.ext import commands
from loguru import logger

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
        Optional[discord.Role]
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
        Optional[Case]
            The latest jail case, or None if not found.
        """
        return await self.db.case.get_latest_case_by_user(
            guild_id=guild_id,
            user_id=user_id,
            # We now filter in controller by latest only; ignore case_types param
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

        await ctx.defer(ephemeral=True)

        # Get jail role
        jail_role = await self.get_jail_role(ctx.guild)
        if not jail_role:
            await ctx.reply("No jail role found.", mention_author=False)
            return

        # Check if user is jailed
        if not await self.is_jailed(ctx.guild.id, member.id):
            await ctx.reply("User is not jailed.", mention_author=False)
            return

        # Permission checks are handled by the @requires_command_permission() decorator
        # Additional validation will be handled by the ModerationCoordinator service

        # Use lock to prevent race conditions
        async def perform_unjail() -> None:
            """Perform the unjail operation with proper error handling."""
            nonlocal ctx, member, jail_role, flags

            # Re-assert guild is not None inside the nested function for type safety
            assert ctx.guild is not None, "Guild context should exist here"
            guild_id = ctx.guild.id

            # Get latest jail case *before* modifying roles
            case = await self.get_latest_jail_case(guild_id, member.id)
            if not case:
                await ctx.reply("No jail case found.", mention_author=False)
                return

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

                    # Restore the role verification logic here
                    # Shorter wait time for roles to be applied by Discord
                    await asyncio.sleep(0.5)

                    # Verify if all roles were successfully added back
                    # Check ctx.guild again for safety within this block
                    if ctx.guild and case.case_user_roles:
                        # Check for missing roles in a simpler way
                        member_role_ids = {role.id for role in member.roles}
                        missing_roles: list[str] = []

                        for role_id in case.case_user_roles:
                            if role_id not in member_role_ids:
                                role = ctx.guild.get_role(role_id)
                                role_name = role.name if role else str(role_id)
                                missing_roles.append(role_name)

                        if missing_roles:
                            missing_str = ", ".join(missing_roles)
                            logger.warning(
                                f"Failed to restore roles for {member}: {missing_str}",
                            )
                            # Optionally notify moderator/user if roles failed to restore
                            # Example: await ctx.send(f"Note: Some roles couldn't be restored: {missing_str}", ephemeral=True)

                elif not restored_roles:
                    logger.warning(
                        f"No roles to restore for {member} or restore action failed partially/completely.",
                    )

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
