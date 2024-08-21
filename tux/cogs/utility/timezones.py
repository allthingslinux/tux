import json
from datetime import datetime
from pathlib import Path

import pytz
from discord.ext import commands

from tux.utils.embeds import EmbedCreator


class Timezones(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def loadjson(self, json_file: str) -> dict:
        """
        Opens the JSON file and returns a dictionary

        Parameters
        ----------
        json_file : str
            The path to the json file
        """

        with Path.open(json_file) as file:
            return json.load(file)

    async def buildtzstring(self, json_file: str) -> str:
        """
        Formats the timezone data within the timezones.json file into a string.

        Parameters
        ----------
        json_file : str
            The path to the json file
        """

        timezone_data = self.loadjson(json_file)

        formatted_lines = []
        utc_now = datetime.now(pytz.utc)

        for entry in timezone_data:
            entry_tz = pytz.timezone(f'{entry["full_timezone"]}')
            entry_time_now = utc_now.astimezone(entry_tz)
            formatted_time = entry_time_now.strftime("%H:%M")
            line = f'{entry["discord_emoji"]} `{entry["offset"]} {entry["timezone"]}` | **{formatted_time}**'
            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    @commands.hybrid_command(name="timezones")
    async def timezones(self, ctx: commands.Context) -> None:
        """
        Presents a list of the top 20 timezones in the world.
        """

        embed = EmbedCreator.create_info_embed(
            title="List of timezones",
            description=await self.buildtzstring("./tux/utils/data/timezones.json"),
            ctx=ctx,
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Timezones(bot))
