import asyncio
import re

import discord
from discord.ext import commands
from loguru import logger
from utils.config import CONFIG


class StatusRoles(commands.Cog):
    """Assign roles to users based on their status."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.status_roles = CONFIG.STATUS_ROLES
        self._unload_task = None  # Store task reference here

        # Check if config exists and is valid
        if not self.status_roles:
            logger.warning("No status roles configurations found. Unloading StatusRoles cog.")
            # Store the task reference
            self._unload_task = asyncio.create_task(self._unload_self())
        else:
            logger.info(f"StatusRoles cog initialized with {len(self.status_roles)} role configurations")

    async def _unload_self(self):
        """Unload this cog if configuration is missing."""
        try:
            await self.bot.unload_extension("tux.cogs.services.status_roles")
            logger.info("StatusRoles cog has been unloaded due to missing configuration")
        except Exception as e:
            logger.error(f"Failed to unload StatusRoles cog: {e}")

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
        logger.trace(f"Presence update for {after.display_name}: {before.status} -> {after.status}")
        # Only process if the custom status changed
        before_status = self.get_custom_status(before)
        after_status = self.get_custom_status(after)

        if before_status != after_status or self.has_activity_changed(before, after):
            logger.trace(f"Status change detected for {after.display_name}: '{before_status}' -> '{after_status}'")
            await self.check_and_update_roles(after)

    def has_activity_changed(self, before: discord.Member, after: discord.Member) -> bool:
        """Check if there was a relevant change in activities."""
        before_has_custom = (
            any(isinstance(a, discord.CustomActivity) for a in before.activities) if before.activities else False
        )
        after_has_custom = (
            any(isinstance(a, discord.CustomActivity) for a in after.activities) if after.activities else False
        )
        return before_has_custom != after_has_custom

    def get_custom_status(self, member: discord.Member) -> str | None:
        """Extract the custom status text from a member's activities."""
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

        for config in self.status_roles:
            # Skip if the config is for a different server
            if int(config.get("server_id", 0)) != member.guild.id:
                continue

            role_id = int(config.get("role_id", 0))
            pattern = str(config.get("status_regex", ".*"))

            role = member.guild.get_role(role_id)
            if not role:
                logger.warning(f"Role {role_id} configured in STATUS_ROLES not found in guild {member.guild.name}")
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
                    logger.info(f"Removing role {role.name} from {member.display_name} (status no longer matches)")
                    await member.remove_roles(role)

            except re.error:
                logger.exception(f"Invalid regex pattern '{pattern}' in STATUS_ROLES config")
            except discord.Forbidden:
                logger.exception(
                    f"Bot lacks permission to modify roles for {member.display_name} in {member.guild.name}",
                )
            except Exception:
                logger.exception(f"Error updating roles for {member.display_name}")


async def setup(bot: commands.Bot):
    await bot.add_cog(StatusRoles(bot))
