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
            ),  # submitted by electron271
            discord.Activity(type=discord.ActivityType.watching, name="All Things Linux"),  # submitted by electron271
            discord.Activity(type=discord.ActivityType.playing, name="with fire"),  # submitted by electron271
            discord.Activity(type=discord.ActivityType.watching, name="linux tech tips"),  # submitted by electron271
            discord.Activity(type=discord.ActivityType.listening, name="mpd"),  # submitted by electron271
            discord.Activity(
                type=discord.ActivityType.watching, name="a vast field of grain"
            ),  # submitted by electron271
            discord.Activity(
                type=discord.ActivityType.playing,
                name="i am calling about your car's extended warranty",
            ),  # submitted by electron271
            discord.Activity(type=discord.ActivityType.playing, name="SuperTuxKart"),  # submitted by electron271
            discord.Activity(type=discord.ActivityType.playing, name="supertux2"),  # submitted by lilliana
            discord.Activity(type=discord.ActivityType.watching, name="Linux install"),  # submitted by electron271
            discord.Activity(type=discord.ActivityType.watching, name="Brodie Robertson"),  # submitted by electron271
            discord.Streaming(
                name="SuperTuxKart", url="https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            ),  # submitted by electron271
            discord.Activity(type=discord.ActivityType.listening, name="Terry Davis on YouTube"),  # submitted by kaizen
            discord.Activity(type=discord.ActivityType.playing, name="with Puffy"),  # submitted by kaizen
            discord.Activity(type=discord.ActivityType.watching, name="the stars"),  # submitted by electron271
            discord.Activity(
                type=discord.ActivityType.playing,
                name="To see who submitted these, check tux/utils/activities.py on the repo (/info tux)",
            ),  # submitted by electron271
        ]

    def get_member_count(self):
        return sum(len(guild.members) for guild in self.bot.guilds)

    async def run(self):
        while True:
            self.activities = self.build_activity_list()
            for activity in self.activities:
                await self.bot.change_presence(activity=activity)
                await asyncio.sleep(self.delay)
