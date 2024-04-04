import discord
from discord.ext import commands
from loguru import logger


class Sync(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="sync", description="Syncs the application commands to Discord.")
    async def sync(self, ctx: commands.Context[commands.Bot], guild: discord.Guild) -> None:
        if ctx.guild:
            self.bot.tree.copy_global_to(guild=ctx.guild)

        await self.bot.tree.sync(guild=ctx.guild)

        logger.info(f"{ctx.author} synced the application command tree.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Sync(bot))
