from discord.ext import commands
from loguru import logger


class Clear(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.has_guild_permissions(administrator=True)
    @commands.command(name="clear", description="Clears the slash command tree.")
    async def clear(self, ctx: commands.Context[commands.Bot]) -> None:
        self.bot.tree.clear_commands(guild=ctx.guild)

        if ctx.guild:
            self.bot.tree.copy_global_to(guild=ctx.guild)

        await self.bot.tree.sync(guild=ctx.guild)

        logger.info(f"{ctx.author} cleared the slash command tree.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Clear(bot))
