import asyncio

import discord
from discord.ext import commands


class ActivityChanger:
    def __init__(self, bot: commands.Bot, delay: int = 5 * 60):
        self.bot = bot
        self.delay = delay
        self.activities = self.build_activity_list()

    def build_activity_list(self):
        return [
            discord.Streaming(name="fortnite gamer hourz", url="https://twitch.tv/urmom"),
            discord.Activity(type=discord.ActivityType.watching, name="All Things Linux"),
            discord.Activity(type=discord.ActivityType.playing, name="with fire"),
            discord.Activity(
                type=discord.ActivityType.watching, name=f"{len(self.bot.users)} members"
            ),
            discord.Activity(type=discord.ActivityType.watching, name="linux tech tips"),
            discord.Activity(type=discord.ActivityType.listening, name="mpd"),
            discord.Activity(type=discord.ActivityType.watching, name="a vast field of grain"),
            discord.Activity(
                type=discord.ActivityType.playing,
                name="i am calling about your car's extended warranty",
            ),
        ]

    async def run(self):
        while True:
            for activity in self.activities:
                await self.bot.change_presence(activity=activity)
                await asyncio.sleep(self.delay)
