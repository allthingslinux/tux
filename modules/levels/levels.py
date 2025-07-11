import datetime

import discord
from bot import Tux
from cogs.services.levels import LevelsService
from database.controllers import DatabaseController
from discord.ext import commands
from ui.embeds import EmbedCreator, EmbedType
from utils import checks
from utils.functions import generate_usage


class Levels(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.levels_service = LevelsService(bot)
        self.db = DatabaseController()
        self.levels.usage = generate_usage(self.levels)
        self.set.usage = generate_usage(self.set)
        self.reset.usage = generate_usage(self.reset)
        self.blacklist.usage = generate_usage(self.blacklist)
        self.set_xp.usage = generate_usage(self.set_xp)

    @commands.hybrid_group(
        name="levels",
        aliases=["lvls"],
    )
    @commands.guild_only()
    async def levels(
        self,
        ctx: commands.Context[Tux],
    ) -> None:
        """
        Level and XP management related commands.
        """

        if ctx.invoked_subcommand is None:
            await ctx.send_help("levels")

    @checks.has_pl(2)
    @commands.guild_only()
    @levels.command(name="set", aliases=["s"])
    async def set(self, ctx: commands.Context[Tux], member: discord.Member, new_level: int) -> None:
        """
        Sets the level of a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to set the level for.
        """

        assert ctx.guild

        old_level: int = await self.db.levels.get_level(member.id, ctx.guild.id)
        old_xp: float = await self.db.levels.get_xp(member.id, ctx.guild.id)

        if embed_result := self.levels_service.valid_xplevel_input(new_level):
            await ctx.send(embed=embed_result)
            return

        new_xp: float = self.levels_service.calculate_xp_for_level(new_level)
        await self.db.levels.update_xp_and_level(
            member.id,
            ctx.guild.id,
            new_xp,
            new_level,
            datetime.datetime.now(datetime.UTC),
        )

        # Update roles based on the new level
        await self.levels_service.update_roles(member, ctx.guild, new_level)

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"Level Set - {member}",
            description=f"{member}'s level has been updated from **{old_level}** to **{new_level}**\nTheir XP has been updated from **{round(old_xp)}** to **{round(new_xp)}**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)

    @checks.has_pl(2)
    @commands.guild_only()
    @levels.command(name="setxp", aliases=["sxp"])
    async def set_xp(self, ctx: commands.Context[Tux], member: discord.Member, xp_amount: int) -> None:
        """
        Sets the xp of a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to set the XP for.
        """
        assert ctx.guild

        if embed_result := self.levels_service.valid_xplevel_input(xp_amount):
            await ctx.send(embed=embed_result)
            return

        old_level: int = await self.db.levels.get_level(member.id, ctx.guild.id)
        old_xp: float = await self.db.levels.get_xp(member.id, ctx.guild.id)

        new_level: int = self.levels_service.calculate_level(xp_amount)
        await self.db.levels.update_xp_and_level(
            member.id,
            ctx.guild.id,
            float(xp_amount),
            new_level,
            datetime.datetime.now(datetime.UTC),
        )

        # Update roles based on the new level
        await self.levels_service.update_roles(member, ctx.guild, new_level)

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"XP Set - {member}",
            description=f"{member}'s XP has been updated from **{round(old_xp)}** to **{(xp_amount)}**\nTheir level has been updated from **{old_level}** to **{new_level}**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)

    @checks.has_pl(2)
    @commands.guild_only()
    @levels.command(name="reset", aliases=["r"])
    async def reset(self, ctx: commands.Context[Tux], member: discord.Member) -> None:
        """
        Resets the xp and level of a member.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to reset the XP for.
        """
        assert ctx.guild

        old_xp: float = await self.db.levels.get_xp(member.id, ctx.guild.id)
        await self.db.levels.reset_xp(member.id, ctx.guild.id)

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"XP Reset - {member}",
            description=f"{member}'s XP has been reset from **{round(old_xp)}** to **0**",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)

    @checks.has_pl(2)
    @commands.guild_only()
    @levels.command(name="blacklist", aliases=["bl"])
    async def blacklist(self, ctx: commands.Context[Tux], member: discord.Member) -> None:
        """
        Blacklists or unblacklists a member from leveling.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object for the command.

        member : discord.Member
            The member to XP blacklist.
        """

        assert ctx.guild

        state: bool = await self.db.levels.toggle_blacklist(member.id, ctx.guild.id)

        embed: discord.Embed = EmbedCreator.create_embed(
            embed_type=EmbedType.INFO,
            title=f"XP Blacklist - {member}",
            description=f"{member} has been {'blacklisted' if state else 'unblacklisted'} from gaining XP.",
            custom_color=discord.Color.blurple(),
        )

        await ctx.send(embed=embed)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Levels(bot))
