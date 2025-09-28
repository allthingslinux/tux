import asyncio
import contextlib
import json

import discord
from discord.ext import commands
from loguru import logger

from tux.core.bot import Tux
from tux.shared.config import CONFIG

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
        self._activity_task: asyncio.Task[None] | None = None
        self._current_index = 0

    @staticmethod
    def build_activity_list() -> list[discord.Activity | discord.Streaming | discord.Game]:
        """Build activity list from config or return default."""
        activities_config = getattr(CONFIG, "ACTIVITIES", None)

        if not activities_config or not str(activities_config).strip():
            return [discord.Game(name="with Linux commands")]

        try:
            activity_data = json.loads(str(activities_config))
        except json.JSONDecodeError:
            logger.error(f"Failed to parse ACTIVITIES JSON: {activities_config!r}")
            return [discord.Game(name="with Linux commands")]

        activities: list[discord.Activity | discord.Streaming | discord.Game] = []
        for data in activity_data:
            activity_type_str = data.get("type", "").lower()
            if activity_type_str == "streaming":
                activities.append(discord.Streaming(name=str(data["name"]), url=str(data["url"])))
            else:
                activity_type = ACTIVITY_TYPE_MAP.get(activity_type_str, discord.ActivityType.playing)
                activities.append(discord.Activity(type=activity_type, name=data["name"]))

        return activities or [discord.Game(name="with Linux commands")]

    def _substitute_placeholders(self, text: str) -> str:
        """Simple synchronous placeholder substitution."""
        if not text:
            return text

        with contextlib.suppress(Exception):
            if "{member_count}" in text:
                member_count = sum(guild.member_count or 0 for guild in self.bot.guilds)
                text = text.replace("{member_count}", str(member_count))
            if "{guild_count}" in text:
                guild_count = len(self.bot.guilds) if self.bot.guilds else 0
                text = text.replace("{guild_count}", str(guild_count))
            if "{bot_name}" in text:
                text = text.replace("{bot_name}", CONFIG.BOT_INFO.BOT_NAME)
            if "{bot_version}" in text:
                text = text.replace("{bot_version}", CONFIG.BOT_INFO.BOT_VERSION)
            if "{prefix}" in text:
                text = text.replace("{prefix}", CONFIG.get_prefix())
        return text

    def _create_activity_with_substitution(
        self,
        activity: discord.Activity | discord.Streaming | discord.Game,
    ) -> discord.Activity | discord.Streaming | discord.Game:
        """Create new activity with substituted name."""
        if not hasattr(activity, "name") or not activity.name:
            return activity

        name = self._substitute_placeholders(activity.name)

        if isinstance(activity, discord.Streaming):
            return discord.Streaming(name=name, url=activity.url)
        return discord.Activity(type=activity.type, name=name)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        """Start activity rotation when bot is ready."""
        if self._activity_task is None or self._activity_task.done():
            logger.info("Starting activity rotation")
            self._activity_task = asyncio.create_task(self._activity_loop())

    async def _activity_loop(self) -> None:
        """Simple activity rotation loop."""
        try:
            await asyncio.sleep(5)  # Wait for bot to be ready

            while True:
                if not self.activities:
                    await asyncio.sleep(self.delay)
                    continue

                activity = self.activities[self._current_index]

                try:
                    new_activity = self._create_activity_with_substitution(activity)
                    await self.bot.change_presence(activity=new_activity)
                    logger.debug(f"Set activity: {new_activity.name}")
                except Exception as e:
                    logger.warning(f"Failed to set activity: {e}")

                self._current_index = (self._current_index + 1) % len(self.activities)
                await asyncio.sleep(self.delay)

        except asyncio.CancelledError:
            logger.info("Activity rotation cancelled")
            raise
        except Exception as e:
            logger.error(f"Activity loop error: {e}")

    async def cog_unload(self) -> None:
        """Cancel activity task when cog is unloaded."""
        if self._activity_task and not self._activity_task.done():
            self._activity_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._activity_task


async def setup(bot: Tux) -> None:
    """Adds the cog to the bot."""
    await bot.add_cog(ActivityHandler(bot))
