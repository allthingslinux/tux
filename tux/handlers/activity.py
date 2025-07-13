import asyncio
import json
from typing import NoReturn

import discord
from discord.ext import commands
from loguru import logger

from tux.bot import Tux
from tux.utils.config import Config
from tux.utils.substitutions import handle_substitution

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
                    if activity.name is None:
                        logger.warning("Activity name is None, skipping this activity.")
                        continue
                    activity.name = await handle_substitution(self.bot, activity.name)
                    await self.bot.change_presence(activity=activity)
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
