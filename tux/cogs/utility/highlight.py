import re

import discord
from discord.ext import commands

from tux.bot import Tux
from tux.utils.flags import generate_usage

highlights = {603229858612510720: ["amy", "amyulated"], 1046905234200469504: ["kai"]}


class Highlight(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.highlight.usage = generate_usage(self.highlight)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if isinstance(message.channel, discord.DMChannel):
            return
        for key, keywords in highlights.items():
            for keyword in keywords:
                regex = r"\b" + re.escape(keyword) + r"\b"
                if re.search(regex, message.content):
                    user = await self.bot.fetch_user(key)
                    await user.send(f"keyword matched({keyword}):\n{message.jump_url}")

    @commands.hybrid_command(
        name="highlight",
    )
    async def highlight(self, ctx: commands.Context[Tux], mode: str, name: str) -> None:
        if mode == "add":
            highlights[ctx.author.id].append(name)
            await ctx.send("highlight added")
        if mode == "remove":
            highlights[ctx.author.id].remove(name)
            await ctx.send("highlight removed")


async def setup(bot: Tux) -> None:
    await bot.add_cog(Highlight(bot))
