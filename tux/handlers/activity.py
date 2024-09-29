import asyncio
from typing import NoReturn

import discord
from discord.ext import commands

from tux.bot import Tux


class ActivityHandler(commands.Cog):
    def __init__(self, bot: Tux, delay: int = 5 * 60) -> None:
        self.bot = bot
        self.delay = delay
        self.activities = self.build_activity_list()

    @staticmethod
    def build_activity_list() -> list[discord.Activity | discord.Streaming]:
        activity_data = [
            {"type": discord.ActivityType.watching, "name": "{member_count} members"},
            {"type": discord.ActivityType.watching, "name": "All Things Linux"},
            {"type": discord.ActivityType.playing, "name": "with fire"},
            {"type": discord.ActivityType.watching, "name": "linux tech tips"},
            {"type": discord.ActivityType.listening, "name": "mpd"},
            {"type": discord.ActivityType.watching, "name": "a vast field of grain"},
            {"type": discord.ActivityType.playing, "name": "i am calling about your car's extended warranty"},
            {"type": discord.ActivityType.playing, "name": "SuperTuxKart"},
            {"type": discord.ActivityType.playing, "name": "SuperTux 2"},
            {"type": discord.ActivityType.watching, "name": "Gentoo compile..."},
            {"type": discord.ActivityType.watching, "name": "Brodie Robertson"},
            {"type": discord.ActivityType.listening, "name": "Terry Davis on YouTube"},
            {"type": discord.ActivityType.playing, "name": "with Puffy"},
            {"type": discord.ActivityType.watching, "name": "the stars"},
            {"type": discord.ActivityType.watching, "name": "VLC"},
            {"type": "streaming", "name": "SuperTuxKart", "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        ]

        activities: list[discord.Activity | discord.Streaming] = []

        for data in activity_data:
            if data["type"] == "streaming":
                activities.append(discord.Streaming(name=str(data["name"]), url=str(data["url"])))
            else:
                activities.append(discord.Activity(type=data["type"], name=data["name"]))
        return activities

    def _get_member_count(self) -> int:
        return sum(guild.member_count for guild in self.bot.guilds if guild.member_count is not None)

    async def run(self) -> NoReturn:
        while True:
            for activity in self.activities:
                if activity.name and "{member_count}" in activity.name:
                    activity.name = activity.name.replace("{member_count}", str(self._get_member_count()))

                await self.bot.change_presence(activity=activity)
                await asyncio.sleep(self.delay)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await asyncio.sleep(5)
        activity_task = asyncio.create_task(self.run())
        await asyncio.gather(activity_task)


async def setup(bot: Tux) -> None:
    await bot.add_cog(ActivityHandler(bot))
