# commands/server.py

import discord
from discord.ext import commands

from tux.command_cog import CommandCog
from tux.utils.tux_logger import TuxLogger

logger = TuxLogger(__name__)


class Server(CommandCog):
    def __init__(self, bot):
        self.bot = bot

    @commands.guild_only()
    @commands.hybrid_command(name="server")
    async def server(self, ctx: commands.Context):
        """
        Sends information about the current Discord Guild.

        Args:
            ctx (commands.Context): The context of where the command was sent.
        """
        if ctx.guild:
            find_bots = sum(1 for member in ctx.guild.members if member.bot)

            embed = discord.Embed()

            if ctx.guild.icon:
                embed.set_thumbnail(url=ctx.guild.icon)
            if ctx.guild.banner:
                embed.set_image(url=ctx.guild.banner.with_format("png").with_size(1024))

            embed.title = ctx.guild.name
            embed.add_field(name="Members", value=ctx.guild.member_count)
            embed.add_field(name="Bots", value=find_bots)
            embed.add_field(name="Boosts", value=ctx.guild.premium_subscription_count)
            embed.add_field(name="Vanity URL", value=ctx.guild.vanity_url_code)
            embed.add_field(name="Owner", value=ctx.guild.owner)
            embed.add_field(
                name="Created", value=ctx.guild.created_at.strftime("%d/%m/%Y")
            )

            embed.set_footer(text=f"Server ID: {ctx.guild.id}")

            await ctx.send(embed=embed)
        else:
            logger.error("Failed to send message: Guild not found.")


async def setup(bot):
    await bot.add_cog(Server(bot))
