import asyncio
import json
from typing import NoReturn

import discord
from discord.ext import commands
from loguru import logger

from core.bot import Tux
from core.config import Config

# Map the string type to the discord.ActivityType enum.
ACTIVITY_TYPE_MAP = {
    "playing": discord.ActivityType.playing,
    "streaming": discord.ActivityType.streaming,
    "listening": discord.ActivityType.listening,
    "watching": discord.ActivityType.watching,
}


class ActivityHandler(commands.Cog):
    def __init__(self, bot: Tux, delay: int = 30) -> None:
        self.bot = bot
        self.delay = delay
        self.activities = self.build_activity_list()
        self._activity_task = None

    @staticmethod
    def build_activity_list() -> list[discord.Activity | discord.Streaming]:
        """
        Parses Config.ACTIVITIES as JSON and returns a list of activity objects

        Returns
        -------
        list[discord.Activity | discord.Streaming]
            A list of activity objects.
        """

        if not Config.ACTIVITIES or not Config.ACTIVITIES.strip():
            logger.warning("Config.ACTIVITIES is empty or None. Returning an empty list.")
            return []

        try:
            activity_data = json.loads(Config.ACTIVITIES)  # Safely parse JSON
        except json.JSONDecodeError:
            logger.error(f"Failed to parse ACTIVITIES JSON: {Config.ACTIVITIES!r}")
            raise  # Re-raise after logging

        activities: list[discord.Activity | discord.Streaming] = []

        for data in activity_data:
            activity_type_str = data.get("type", "").lower()
            if activity_type_str == "streaming":
                activities.append(discord.Streaming(name=str(data["name"]), url=str(data["url"])))
            else:
                # Map the string to the discord.ActivityType enum; default to "playing" if not found.
                activity_type = ACTIVITY_TYPE_MAP.get(activity_type_str, discord.ActivityType.playing)
                activities.append(discord.Activity(type=activity_type, name=data["name"]))

        return activities

    def _get_member_count(self) -> int:
        """
        Returns the total member count of all guilds the bot is in.

        Returns
        -------
        int
            The total member count of all guilds the bot is in.
        """
        return sum(guild.member_count for guild in self.bot.guilds if guild.member_count is not None)

    async def handle_substitution(
        self,
        activity: discord.Activity | discord.Streaming,
    ) -> discord.Activity | discord.Streaming:
        """
        Replaces multiple placeholders in the activity name.

        Parameters
        ----------
        activity : discord.Activity | discord.Streaming
            The activity to handle substitutions for.

        Returns
        -------
        discord.Activity | discord.Streaming
            The activity with substitutions applied.
        """

        # Available substitutions:
        # {member_count} - total member count of all guilds
        # {guild_count} - total guild count
        # {bot_name} - bot name
        # {bot_version} - bot version
        # {prefix} - bot prefix

        if activity.name and "{member_count}" in activity.name:
            activity.name = activity.name.replace("{member_count}", str(self._get_member_count()))
        if activity.name and "{guild_count}" in activity.name:
            activity.name = activity.name.replace("{guild_count}", str(len(self.bot.guilds)))
        if activity.name and "{bot_name}" in activity.name:
            activity.name = activity.name.replace("{bot_name}", Config.BOT_NAME)
        if activity.name and "{bot_version}" in activity.name:
            activity.name = activity.name.replace("{bot_version}", Config.BOT_VERSION)
        if activity.name and "{prefix}" in activity.name:
            activity.name = activity.name.replace("{prefix}", Config.DEFAULT_PREFIX)

        return activity

    async def run(self) -> NoReturn:
        """
        Loops through activities and updates bot presence periodically.

        Parameters
        ----------
        self : ActivityHandler
            The ActivityHandler instance.

        Returns
        -------
        NoReturn
        """

        while True:
            for activity in self.activities:
                try:
                    substituted_activity = await self.handle_substitution(activity)
                    await self.bot.change_presence(activity=substituted_activity)
                except Exception as e:
                    logger.error(f"Error updating activity: {e}")
                    # Continue the loop even if an error occurs

                await asyncio.sleep(self.delay)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if self._activity_task is None or self._activity_task.done():
            self._activity_task = asyncio.create_task(self._delayed_start())

    async def _delayed_start(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(5)  # Optional: extra delay for safety
        await self.run()


async def setup(bot: Tux) -> None:
    """Adds the cog to the bot."""
    await bot.add_cog(ActivityHandler(bot))
