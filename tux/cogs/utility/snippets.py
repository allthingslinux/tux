import datetime
import string

import discord
from discord import AllowedMentions
from discord.ext import commands
from loguru import logger

from prisma.models import Snippets as SnippetsModel
from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator


class Snippets(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db_controller = DatabaseController().snippets

    @commands.command(
        name="snippets",
        usage="$ls [page]",
        description="List snippets by page (max 10).",
        aliases=["ls"],
    )
    async def list_snippets(self, ctx: commands.Context[commands.Bot], page: int = 1) -> None:
        """
        List snippets by page (max 10).

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object.
        page : int, optional
            The page number, by default 1.
        """

        snippets: list[SnippetsModel] = await self.db_controller.get_all_snippets_sorted(
            newestfirst=True
        )

        # Calculate the number of pages based on the number of snippets
        pages = 1 if len(snippets) <= 10 else len(snippets) // 10 + 1

        # If there are no snippets, send an error message
        if not snippets:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="No snippets found.", ctx=ctx
            )
            await ctx.send(embed=embed)
            return

        # If the page number is invalid, send an error message
        if page < 1 or page > pages:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Invalid page number.", ctx=ctx
            )
            await ctx.send(embed=embed)
            return

        # Get the snippets for the specified page
        snippets = snippets[(page - 1) * 10 : page * 10]

        # Snippets:
        # `01. snippet_name        | author: author_name`
        # `02. longer_snippet_name | author: author_name`

        embed = EmbedCreator.create_info_embed(
            title="Snippets",
            description="\n".join(
                [
                    f"`{str(index + 1).zfill(2)}. {snippet.name.ljust(20)} | author: {self.bot.get_user(snippet.author_id) or 'Unknown'}`"
                    for index, snippet in enumerate(snippets)
                ]
            ),
            ctx=ctx,
        )
        embed.set_footer(text=f"Page {page}/{pages}")

        await ctx.send(embed=embed)

    @commands.command(
        name="deletesnippet", usage="$ds <name>", description="Delete a snippet.", aliases=["ds"]
    )
    async def delete_snippet(self, ctx: commands.Context[commands.Bot], name: str) -> None:
        """
        Delete a snippet.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object.
        name : str
            The name of the snippet.
        """

        snippet = await self.db_controller.get_snippet_by_name(name)

        if snippet is None:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Snippet not found.", ctx=ctx
            )
            await ctx.send(embed=embed)
            return

        # Check if the author of the snippet is the same as the user who wants to delete it and if theres no author don't allow deletion
        author_id = snippet.author_id or 0
        if author_id != ctx.author.id:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="You can only delete your own snippets.", ctx=ctx
            )
            await ctx.send(embed=embed)
            return

        await self.db_controller.delete_snippet(name)

        await ctx.send("Snippet deleted.")
        logger.info(f"{ctx.author} deleted the snippet with the name {name}.")

    @commands.command(
        name="snippet", usage="$s <name>", description="Get a snippet.", aliases=["s"]
    )
    async def get_snippet(self, ctx: commands.Context[commands.Bot], name: str) -> None:
        """
        Get a snippet.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object.
        name : str
            The name of the snippet.
        """

        snippet = await self.db_controller.get_snippet_by_name(name)

        if snippet is None:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Snippet not found.", ctx=ctx
            )
            await ctx.send(embed=embed)
            return

        top_row = f"`/snippets/{snippet.name}.txt` |⦚| {self.bot.get_user(snippet.author_id) or 'Unknown Author'}"

        text = f"{top_row}\n{snippet.content}"

        await ctx.send(text, allowed_mentions=AllowedMentions.none())

    @commands.command(
        name="snippetinfo",
        usage="$si <name>",
        description="Get information about a snippet.",
        aliases=["si"],
    )
    async def get_snippet_info(self, ctx: commands.Context[commands.Bot], name: str) -> None:
        """
        Get information about a snippet.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object.
        name : str
            The name of the snippet.
        """

        snippet = await self.db_controller.get_snippet_by_name(name)

        if snippet is None:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Snippet not found.", ctx=ctx
            )
            await ctx.send(embed=embed)
            return

        author = self.bot.get_user(snippet.author_id) or ctx.author

        embed: discord.Embed = EmbedCreator.custom_footer_embed(
            title="Snippet Information",
            content=f"**Name:** {snippet.name}\n**Author:** {author}\n**Created At:** (set as embed timestamp)\n**Content:** {snippet.content}",
            ctx=ctx,
            latency="N/A",
            interaction=None,
            state="DEBUG",
            user=author,
        )

        embed.timestamp = snippet.created_at or datetime.datetime.fromtimestamp(0, datetime.UTC)

        await ctx.send(embed=embed)

    @commands.command(
        name="createsnippet",
        usage="$cs <name> <content>",
        description="Create a snippet.",
        aliases=["cs"],
    )
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

        args = arg.split(" ")
        if len(args) < 2:
            embed = EmbedCreator.create_error_embed(
                title="Error",
                description="Please provide a name and content for the snippet.",
                ctx=ctx,
            )
            await ctx.send(embed=embed)
            return

        name = args[0]
        content = " ".join(args[1:])
        created_at = datetime.datetime.now(datetime.UTC)
        author_id = ctx.author.id

        # Check if the snippet already exists
        if await self.db_controller.get_snippet_by_name(name) is not None:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Snippet already exists.", ctx=ctx
            )
            await ctx.send(embed=embed)
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

        await self.db_controller.create_snippet(
            name=name,
            content=content,
            created_at=created_at,
            author_id=author_id,
        )

        await ctx.send("Snippet created.")
        logger.info(f"{ctx.author} created a snippet with the name {name} and content {content}.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Snippets(bot))
