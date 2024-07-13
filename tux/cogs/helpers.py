import discord
from discord.ext import commands
from loguru import logger


class Helpers(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def get_guild_from_int(self, guild_id: int) -> discord.Guild | None:
        try:
            guild = self.bot.get_guild(guild_id)
        except Exception as error:
            logger.error(f"Failed to get guild from id. Error: {error}")
            return None

        return guild

    async def get_or_fetch_member(
        self,
        guild: discord.Guild | None,
        user_id: int,
    ) -> discord.Member | discord.User | None:
        if not guild:
            return None

        member = guild.get_member(user_id)
        if not member:
            try:
                member = await guild.fetch_member(user_id)
            except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                return None
        return member

    async def get_member_from_ctx(self, ctx: commands.Context[commands.Bot]) -> discord.Member | None:
        if ctx.guild:
            member = ctx.guild.get_member(ctx.author.id)
            if not member:
                try:
                    member = await ctx.guild.fetch_member(ctx.author.id)
                except (discord.HTTPException, discord.NotFound, discord.Forbidden):
                    return None
            return member
        return None


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Helpers(bot))
