import discord
from bot import Tux
from cogs.services.levels import LevelsService
from database.controllers import DatabaseController
from discord.ext import commands
from ui.embeds import EmbedCreator, EmbedType
from utils.config import CONFIG
from utils.functions import generate_usage


class Level(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_service = LevelsService(bot)
        self.db = DatabaseController()
        self.level.usage = generate_usage(self.level)

    @commands.guild_only()
    @commands.hybrid_command(
        name="level",
        aliases=["lvl", "rank", "xp"],
    )
    async def level(self, ctx: commands.Context[Tux], member: discord.User | discord.Member | None = None) -> None:
        """
        Fetches the XP and level for a member (or the person who runs the command if no member is provided).

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.User
            The member to fetch XP and level for.
        """

        if ctx.guild is None:
            await ctx.send("This command can only be executed within a guild.")
            return

        if member is None:
            member = ctx.author

        xp: float = await self.db.levels.get_xp(member.id, ctx.guild.id)
        level: int = await self.db.levels.get_level(member.id, ctx.guild.id)

        if self.levels_service.enable_xp_cap and level >= self.levels_service.max_level:
            max_xp: float = self.levels_service.calculate_xp_for_level(self.levels_service.max_level)
            level_display: int = self.levels_service.max_level
            xp_display: str = f"{round(max_xp)} (limit reached)"
        else:
            level_display: int = level
            xp_display: str = f"{round(xp)}"

        if CONFIG.SHOW_XP_PROGRESS:
            xp_progress: int
            xp_required: int
            xp_progress, xp_required = self.levels_service.get_level_progress(xp, level)
            progress_bar: str = self.levels_service.generate_progress_bar(xp_progress, xp_required)

            embed: discord.Embed = EmbedCreator.create_embed(
                embed_type=EmbedType.DEFAULT,
                title=f"Level {level_display}",
                description=f"Progress to Next Level:\n{progress_bar}",
                custom_color=discord.Color.blurple(),
                custom_author_text=f"{member.name}",
                custom_author_icon_url=member.display_avatar.url,
                custom_footer_text=f"Total XP: {xp_display}",
            )
        else:
            embed: discord.Embed = EmbedCreator.create_embed(
                embed_type=EmbedType.DEFAULT,
                description=f"**Level {level_display}** - `XP: {xp_display}`",
                custom_color=discord.Color.blurple(),
                custom_author_text=f"{member.name}",
                custom_author_icon_url=member.display_avatar.url,
            )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Level(bot))
