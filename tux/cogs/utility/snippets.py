import datetime
import string

import discord
from discord import AllowedMentions
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu

from prisma.models import Snippet
from tux.database.controllers import DatabaseController
from tux.utils import checks
from tux.utils.constants import Constants as CONST
from tux.utils.embeds import EmbedCreator, create_embed_footer


class Snippets(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = DatabaseController().snippet
        self.config = DatabaseController().guild_config

    @commands.command(
        name="snippets",
        aliases=["ls"],
        usage="$snippets",
    )
    @commands.guild_only()
    async def list_snippets(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        List snippets by pagination.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object.
        """

        if ctx.guild is None:
            await ctx.send("This command cannot be used in direct messages.")
            return

        snippets: list[Snippet] = await self.db.get_all_snippets_sorted(newestfirst=True)

        # Remove snippets that are not in the current server
        snippets = [snippet for snippet in snippets if snippet.guild_id == ctx.guild.id]

        # If there are no snippets, send an error message
        if not snippets:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="No snippets found.",
                ctx=ctx,
            )
            await ctx.send(embed=embed, delete_after=30)
            return

        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)

        snippets_per_page = 10
        for i in range(0, len(snippets), snippets_per_page):
            embed = self._create_snippets_list_embed(ctx, snippets[i : i + snippets_per_page], len(snippets))
            menu.add_page(embed)

        menu.add_button(ViewButton.go_to_first_page())
        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())
        menu.add_button(ViewButton.go_to_last_page())
        menu.add_button(ViewButton.end_session())

        await menu.start()

    def _create_snippets_list_embed(
        self,
        ctx: commands.Context[commands.Bot],
        snippets: list[Snippet],
        total_snippets: int,
    ) -> discord.Embed:
        embed = discord.Embed(
            title=f"Total Snippets ({total_snippets})",
            description="",
            color=CONST.EMBED_COLORS["DEFAULT"],
        )

        if ctx.guild:
            embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon)

        footer_text, footer_icon_url = create_embed_footer(ctx)
        embed.set_footer(text=footer_text, icon_url=footer_icon_url)
        embed.timestamp = ctx.message.created_at

        description = "```\n"

        for snippet in snippets:
            author = self.bot.get_user(snippet.snippet_user_id) or "Unknown"
            description += f"{snippet.snippet_name.ljust(20)} | by: {author}\n"

        description += "```"

        embed.description = description

        return embed

    @commands.command(
        name="deletesnippet",
        aliases=["ds"],
        usage="$deletesnippet [name]",
    )
    @commands.guild_only()
    async def delete_snippet(self, ctx: commands.Context[commands.Bot], name: str) -> None:
        """
        Delete a snippet by name.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object.
        name : str
            The name of the snippet.
        """

        if ctx.guild is None:
            await ctx.send("This command cannot be used in direct messages.")
            return

        snippet = await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id)

        if snippet is None:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="Snippet not found.",
                ctx=ctx,
            )

            await ctx.send(embed=embed, delete_after=30, ephemeral=True)
            return

        # Check if the author of the snippet is the same as the user who wants to delete it and if theres no author don't allow deletion
        author_id = snippet.snippet_user_id or 0
        if author_id != ctx.author.id:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="You can only delete your own snippets.",
                ctx=ctx,
            )
            await ctx.send(embed=embed, delete_after=30, ephemeral=True)
            return

        await self.db.delete_snippet_by_id(snippet.snippet_id)

        await ctx.send("Snippet deleted.", delete_after=30, ephemeral=True)
        logger.info(f"{ctx.author} deleted the snippet with the name {name}.")

    @commands.command(
        name="forcedeletesnippet",
        aliases=["fds"],
        usage="$forcedeletesnippet [name]",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def force_delete_snippet(self, ctx: commands.Context[commands.Bot], name: str) -> None:
        """
        Force delete a snippet by name.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object.
        name : str
            The name of the snippet.
        """

        if ctx.guild is None:
            await ctx.send("This command cannot be used in direct messages.")
            return

        snippet = await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id)

        if snippet is None:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="Snippet not found.",
                ctx=ctx,
            )
            await ctx.send(embed=embed, delete_after=30, ephemeral=True)
            return

        await self.db.delete_snippet_by_id(snippet.snippet_id)

        await ctx.send("Snippet deleted.", delete_after=30, ephemeral=True)
        logger.info(f"{ctx.author} force deleted the snippet with the name {name}.")

    @commands.command(
        name="snippet",
        aliases=["s"],
        usage="$snippet [name]",
    )
    @commands.guild_only()
    async def get_snippet(self, ctx: commands.Context[commands.Bot], name: str) -> None:
        """
        Get a snippet by name.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object.
        name : str
            The name of the snippet.
        """

        if ctx.guild is None:
            await ctx.send("This command cannot be used in direct messages.")
            return

        snippet = await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id)

        if snippet is None:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="Snippet not found.",
                ctx=ctx,
            )
            await ctx.send(embed=embed, delete_after=30, ephemeral=True)
            return

        text = f"`/snippets/{snippet.snippet_name}.txt` || {snippet.snippet_content}"

        await ctx.send(text, allowed_mentions=AllowedMentions.none())

    @commands.command(
        name="snippetinfo",
        aliases=["si"],
        usage="$snippetinfo [name]",
    )
    @commands.guild_only()
    async def get_snippet_info(self, ctx: commands.Context[commands.Bot], name: str) -> None:
        """
        Get information about a snippet by name.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object.
        name : str
            The name of the snippet.
        """

        if ctx.guild is None:
            await ctx.send("This command cannot be used in direct messages.")
            return

        snippet = await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id)

        if snippet is None:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="Snippet not found.",
                ctx=ctx,
            )
            await ctx.send(embed=embed, delete_after=30)
            return

        author = self.bot.get_user(snippet.snippet_user_id) or ctx.author

        latency = round(int(ctx.bot.latency * 1000))

        embed: discord.Embed = EmbedCreator.custom_footer_embed(
            title="Snippet Information",
            ctx=ctx,
            latency=f"{latency}ms",
            interaction=None,
            state="DEFAULT",
            user=author,
        )

        embed.add_field(name="Name", value=snippet.snippet_name, inline=False)
        embed.add_field(name="Author", value=f"{author.mention}", inline=False)
        embed.add_field(name="Content", value=f"> {snippet.snippet_content}", inline=False)

        embed.timestamp = snippet.snippet_created_at or datetime.datetime.fromtimestamp(
            0,
            datetime.UTC,
        )

        await ctx.send(embed=embed)

    @commands.command(
        name="createsnippet",
        aliases=["cs"],
        usage="$createsnippet [name] [content]",
    )
    @commands.guild_only()
    async def create_snippet(self, ctx: commands.Context[commands.Bot], *, arg: str) -> None:
        """
        Create a snippet.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object.
        arg : str
            The name and content of the snippet.
        """

        if ctx.guild is None:
            await ctx.send("This command cannot be used in direct messages.")
            return

        args = arg.split(" ")
        if len(args) < 2:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="Please provide a name and content for the snippet.",
                ctx=ctx,
            )
            await ctx.send(embed=embed, delete_after=30, ephemeral=True)
            return

        name = args[0]
        content = " ".join(args[1:])
        created_at = datetime.datetime.now(datetime.UTC)
        author_id = ctx.author.id
        server_id = ctx.guild.id

        # Check if the snippet already exists
        if await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id) is not None:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="Snippet already exists.",
                ctx=ctx,
            )
            await ctx.send(embed=embed, delete_after=30, ephemeral=True)
            return

        # Check if the name is longer than 20 characters and includes non-alphanumeric characters (except -_)
        rules = set(string.ascii_letters + string.digits + "-_")

        if len(name) > 20 or any(char not in rules for char in name):
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="Snippet name must be alphanumeric (allows dashes and underscores) and less than 20 characters.",
            )
            await ctx.send(embed=embed)
            return

        await self.db.create_snippet(
            snippet_name=name,
            snippet_content=content,
            snippet_created_at=created_at,
            snippet_user_id=author_id,
            guild_id=server_id,
        )

        await ctx.send("Snippet created.", delete_after=30, ephemeral=True)
        logger.info(f"{ctx.author} created a snippet with the name {name} and content {content}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Snippets(bot))
