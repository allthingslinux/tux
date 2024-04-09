import asyncio

import discord
from discord.ext import commands


class ActivityChanger:
    def __init__(self, bot: commands.Bot, delay: int = 5 * 60):
        self.bot = bot
        self.delay = delay

    def build_activity_list(self):
        return [
            discord.Activity(
                type=discord.ActivityType.watching, name=f"{self.get_member_count()} members"
            ),
            discord.Streaming(name="fortnite gamer hourz", url="https://twitch.tv/urmom"),
            discord.Activity(type=discord.ActivityType.watching, name="All Things Linux"),
            discord.Activity(type=discord.ActivityType.playing, name="with fire"),
            discord.Activity(type=discord.ActivityType.watching, name="linux tech tips"),
            discord.Activity(type=discord.ActivityType.listening, name="mpd"),
            discord.Activity(type=discord.ActivityType.watching, name="a vast field of grain"),
            discord.Activity(
                type=discord.ActivityType.playing,
                name="i am calling about your car's extended warranty",
            ),
        ]

    def get_member_count(self):
        return sum(len(guild.members) for guild in self.bot.guilds)

    async def run(self):
        while True:
            self.activities = self.build_activity_list()
            for activity in self.activities:
                await self.bot.change_presence(activity=activity)
                await asyncio.sleep(self.delay)
