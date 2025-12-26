"""
Automatic role assignment based on user status.

This module automatically assigns roles to users based on their Discord
custom status messages, supporting regex pattern matching and role management.
"""

import re

import discord
from discord.ext import commands
from loguru import logger

from tux.core.base_cog import BaseCog
from tux.core.bot import Tux
from tux.services.sentry import capture_exception_safe
from tux.shared.config import CONFIG


class StatusRoles(BaseCog):
    """Assign roles to users based on their status."""

    def __init__(self, bot: Tux) -> None:
        """Initialize the status roles service.

        Parameters
        ----------
        bot : Tux
            The bot instance to attach this service to.
        """
        super().__init__(bot)

        # Check if mappings exist and are valid
        if self.unload_if_missing_config(
            condition=not CONFIG.STATUS_ROLES.MAPPINGS,
            config_name="Status role mappings",
        ):
            return

        logger.info(
            f"StatusRoles cog initialized with {len(CONFIG.STATUS_ROLES.MAPPINGS)} mappings",
        )

    @commands.Cog.listener()
    async def on_ready(self):
        """Check all users' statuses when the bot starts up."""
        logger.info("StatusRoles cog ready, checking all users' statuses")
        for guild in self.bot.guilds:
            for member in guild.members:
                await self.check_and_update_roles(member)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Event triggered when a user's presence changes."""
        logger.trace(
            f"Presence update for {after.display_name}: {before.status} -> {after.status}",
        )
        # Only process if the custom status changed
        before_status = self.get_custom_status(before)
        after_status = self.get_custom_status(after)

        if before_status != after_status or self.has_activity_changed(before, after):
            logger.trace(
                f"Status change detected for {after.display_name}: '{before_status}' -> '{after_status}'",
            )
            await self.check_and_update_roles(after)

    def has_activity_changed(
        self,
        before: discord.Member,
        after: discord.Member,
    ) -> bool:
        """
        Check if there was a relevant change in activities.

        Returns
        -------
        bool
            True if custom activity status changed, False otherwise.
        """
        before_has_custom = (
            any(isinstance(a, discord.CustomActivity) for a in before.activities)
            if before.activities
            else False
        )
        after_has_custom = (
            any(isinstance(a, discord.CustomActivity) for a in after.activities)
            if after.activities
            else False
        )
        return before_has_custom != after_has_custom

    def get_custom_status(self, member: discord.Member) -> str | None:
        """
        Extract the custom status text from a member's activities.

        Returns
        -------
        str | None
            The custom status text, or None if not found.
        """
        if not member.activities:
            return None

        return next(
            (
                activity.name
                for activity in member.activities
                if isinstance(activity, discord.CustomActivity) and activity.name
            ),
            None,
        )

    async def check_and_update_roles(self, member: discord.Member):
        """Check a member's status against configured patterns and update roles accordingly."""
        if member.bot:
            return

        status_text = self.get_custom_status(member)
        if status_text is None:
            status_text = ""  # Use empty string for regex matching if no status

        for mapping in CONFIG.STATUS_ROLES.MAPPINGS:
            # Skip if the mapping is for a different server
            if int(mapping.get("server_id", 0)) != member.guild.id:
                continue

            role_id = int(mapping.get("role_id", 0))
            pattern = str(mapping.get("status_regex", ".*"))

            role = member.guild.get_role(role_id)
            if not role:
                logger.warning(
                    f"Role {role_id} configured in status roles not found in guild {member.guild.name}",
                )
                continue

            try:
                matches = bool(re.search(pattern, status_text, re.IGNORECASE))

                has_role = role in member.roles

                if matches and not has_role:
                    # Add role if status matches and member doesn't have the role
                    logger.info(
                        f"Adding role {role.name} to {member.display_name} (status: '{status_text}' matched '{pattern}')",
                    )
                    await member.add_roles(role)

                elif not matches and has_role:
                    # Remove role if status doesn't match and member has the role
                    logger.info(
                        f"Removing role {role.name} from {member.display_name} (status no longer matches)",
                    )
                    await member.remove_roles(role)

            except re.error:
                # Configuration error - don't send to Sentry
                logger.warning(
                    f"Invalid regex pattern '{pattern}' in STATUS_ROLES config",
                )
            except discord.Forbidden:
                # User error (permission denied) - don't send to Sentry
                logger.warning(
                    f"Bot lacks permission to modify roles for {member.display_name} in {member.guild.name}",
                )
            except Exception as e:
                # Unexpected error - send to Sentry
                logger.error(f"Error updating roles for {member.display_name}: {e}")

                capture_exception_safe(
                    e,
                    extra_context={
                        "operation": "update_status_roles",
                        "member_id": str(member.id),
                        "guild_id": str(member.guild.id),
                        "pattern": pattern,
                    },
                )


async def setup(bot: Tux) -> None:
    """Set up the StatusRoles cog.

    Parameters
    ----------
    bot : Tux
        The bot instance to add the cog to.
    """
    await bot.add_cog(StatusRoles(bot))
