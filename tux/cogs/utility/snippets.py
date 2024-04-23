import datetime
import string

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
        name="snippets", description="List snippets by page (max 10).", aliases=["ss"]
    )
    async def list_snippets(self, ctx: commands.Context[commands.Bot], page: int = 1) -> None:
        snippets: list[SnippetsModel] = await self.db_controller.get_all_snippets()

        # sort the snippets by time created
        snippets: list[SnippetsModel] = sorted(snippets, key=lambda x: x.created_at, reverse=True)

        # calculate the number of pages
        # if there are no or less than 10 snippets, there is only one page
        pages = 1 if len(snippets) <= 10 else len(snippets) // 10 + 1

        # if no snippets are found
        if not snippets:
            embed = EmbedCreator.create_error_embed(title="Error", description="No snippets found.")
            await ctx.send(embed=embed)
            return

        # if the page is out of bounds
        if page < 1 or page > pages:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Invalid page number."
            )
            await ctx.send(embed=embed)
            return

        # get the snippets for the specified page
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
        )
        embed.set_footer(text=f"Page {page}/{pages}")

        await ctx.send(embed=embed)

    @commands.command(name="deletesnippet", description="Delete a snippet.", aliases=["ds"])
    async def delete_snippet(self, ctx: commands.Context[commands.Bot], name: str) -> None:
        snippet = await self.db_controller.get_snippet_by_name(name)

        if snippet is None:
            embed = EmbedCreator.create_error_embed(title="Error", description="Snippet not found.")
            await ctx.send(embed=embed)
            return

        # check if the author of the snippet is the same as the user who wants to delete it, and if theres no author dont allow deletion
        author_id = snippet.author_id or 0
        if author_id != ctx.author.id:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="You can only delete your own snippets."
            )
            await ctx.send(embed=embed)
            return

        await self.db_controller.delete_snippet(name)
        logger.info(f"{ctx.author} deleted the snippet with the name {name}.")
        await ctx.send("Snippet deleted.")

    @commands.command(name="snippet", description="Get a snippet.", aliases=["s"])
    async def get_snippet(self, ctx: commands.Context[commands.Bot], name: str) -> None:
        snippet = await self.db_controller.get_snippet_by_name(name)

        if snippet is None:
            embed = EmbedCreator.create_error_embed(title="Error", description="Snippet not found.")
            await ctx.send(embed=embed)
            return

        embed = EmbedCreator.custom_footer_embed(
            ctx=None,
            interaction=None,
            state="DEFAULT",
            user=self.bot.get_user(snippet.author_id) or ctx.author,
            content=snippet.content,
            title=snippet.name,
            latency="N/A",
        )

        await ctx.send(embed=embed)

    @commands.command(name="createsnippet", description="Create a snippet.", aliases=["cs"])
    async def create_snippet(self, ctx: commands.Context[commands.Bot], *args: str) -> None:
        if len(args) < 2:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Please provide a name and content for the snippet."
            )
            await ctx.send(embed=embed)
            return

        name = args[0]
        content = " ".join(args[1:])
        created_at = datetime.datetime.now(datetime.UTC)
        author_id = ctx.author.id

        # check if the snippet already exists
        if await self.db_controller.get_snippet_by_name(name) is not None:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Snippet already exists."
            )
            await ctx.send(embed=embed)
            return

        # check if the name is longer than 20 characters and includes non-alphanumeric characters (except -_)
        rules = set(string.ascii_letters + string.digits + "-_")
        if len(name) > 20 or not all(char in rules for char in name):
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

        logger.info(f"{ctx.author} created a snippet with the name {name} and content {content}.")
        await ctx.send("Snippet created.")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Snippets(bot))
