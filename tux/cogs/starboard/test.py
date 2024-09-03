from typing import cast

import discord
from discord.ext import commands

from tux.bot import Tux
from tux.ui.starboard.image_gen import generate_discord_message_image


class Starboard(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot

    @commands.hybrid_command(
        name="test",
        usage="test",
    )
    async def ping(self, ctx: commands.Context[Tux], *, message: str) -> None:
        # nickname: str, pfp_url: str, role_color: str, message_content: str, image_attachment_url: str | None = None

        member = cast(discord.Member, ctx.author)

        nickname = member.display_name
        pfp_url = member.display_avatar.url

        role_color = next(
            (f"#{role.color.value:06X}" for role in reversed(member.roles) if role.color != discord.Color.default()),
            "#FFFFFF",
        )
        message_content = message
        image_attachment_url = None

        image = generate_discord_message_image(nickname, pfp_url, role_color, message_content, image_attachment_url)

        image.save("image.png")
        await ctx.send(file=discord.File("image.png"))


async def setup(bot: Tux) -> None:
    await bot.add_cog(Starboard(bot))
