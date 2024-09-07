import contextlib
import datetime
import string

import discord
from discord import AllowedMentions
from discord.ext import commands
from loguru import logger
from reactionmenu import ViewButton, ViewMenu

from prisma.enums import CaseType
from prisma.models import Snippet
from tux.bot import Tux
from tux.database.controllers import CaseController, DatabaseController
from tux.ui.embeds import EmbedCreator, EmbedType
from tux.utils import checks


class Snippets(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController().snippet
        self.config = DatabaseController().guild_config
        self.case_controller = CaseController()

    async def is_snippetbanned(self, guild_id: int, user_id: int) -> bool:
        ban_cases = await self.case_controller.get_all_cases_by_type(guild_id, CaseType.SNIPPETBAN)
        unban_cases = await self.case_controller.get_all_cases_by_type(guild_id, CaseType.SNIPPETUNBAN)

        ban_count = sum(case.case_user_id == user_id for case in ban_cases)
        unban_count = sum(case.case_user_id == user_id for case in unban_cases)

        return ban_count > unban_count

    @commands.command(
        name="snippets",
        aliases=["ls"],
        usage="snippets",
    )
    @commands.guild_only()
    async def list_snippets(self, ctx: commands.Context[Tux]) -> None:
        """
        List snippets by pagination.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        """

        assert ctx.guild

        snippets: list[Snippet] = await self.db.get_all_snippets_sorted(newestfirst=True)

        # Remove snippets that are not in the current server
        snippets = [snippet for snippet in snippets if snippet.guild_id == ctx.guild.id]

        # If there are no snippets, return
        if not snippets:
            await self.send_snippet_error(ctx, description="No snippets found.")
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
        ctx: commands.Context[Tux],
        snippets: list[Snippet],
        total_snippets: int,
    ) -> discord.Embed:
        assert ctx.guild
        assert ctx.guild.icon

        description = "```\n"

        for snippet in snippets:
            author = self.bot.get_user(snippet.snippet_user_id) or "Unknown"
            description += f"{snippet.snippet_name.ljust(20)} | by: {author}\n"

        description += "```"

        footer_text, footer_icon_url = EmbedCreator.get_footer(
            bot=ctx.bot,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
        )

        return EmbedCreator.create_embed(
            embed_type=EmbedType.DEFAULT,
            title=f"Total Snippets ({total_snippets})",
            description=description,
            custom_author_text=ctx.guild.name,
            custom_author_icon_url=ctx.guild.icon.url,
            message_timestamp=ctx.message.created_at,
            custom_footer_text=footer_text,
            custom_footer_icon_url=footer_icon_url,
        )

    @commands.command(
        name="topsnippets",
        aliases=["ts"],
        usage="topsnippets",
    )
    @commands.guild_only()
    async def top_snippets(self, ctx: commands.Context[Tux]) -> None:
        """
        List top snippets.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        """
        assert ctx.guild

        # find the top 10 snippets by uses
        snippets: list[Snippet] = await self.db.get_all_snippets_by_guild_id(ctx.guild.id)

        # If there are no snippets, return
        if not snippets:
            await self.send_snippet_error(ctx, description="No snippets found.")
            return

        # sort the snippets by uses
        snippets.sort(key=lambda x: x.uses, reverse=True)

        # print in this format
        # 1. snippet_name | uses: 10
        # 2. snippet_name | uses: 9
        # 3. snippet_name | uses: 8
        # ...

        text = "```\n"
        for i, snippet in enumerate(snippets[:10]):
            text += f"{i+1}. {snippet.snippet_name.ljust(20)} | uses: {snippet.uses}\n"
        text += "```"

        # only show top 10, no pagination
        embed = EmbedCreator.create_embed(
            embed_type=EmbedType.DEFAULT,
            title="Top Snippets",
            description=text,
            hide_author=True,
        )

        await ctx.send(embed=embed)

    @commands.command(
        name="deletesnippet",
        aliases=["ds"],
        usage="deletesnippet [name]",
    )
    @commands.guild_only()
    async def delete_snippet(self, ctx: commands.Context[Tux], name: str) -> None:
        """
        Delete a snippet by name.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        name : str
            The name of the snippet.
        """

        assert ctx.guild

        snippet = await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id)

        if snippet is None:
            await self.send_snippet_error(ctx, description="Snippet not found.")
            return

        # check if the snippet is locked
        if snippet.locked:
            await self.send_snippet_error(
                ctx,
                description="This snippet is locked and cannot be deleted. If you are a moderator you can use the `forcedeletesnippet` command.",
            )
            return

        # Check if the author of the snippet is the same as the user who wants to delete it and if theres no author don't allow deletion
        author_id = snippet.snippet_user_id or 0
        if author_id != ctx.author.id:
            await self.send_snippet_error(ctx, description="You can only delete your own snippets.")
            return

        await self.db.delete_snippet_by_id(snippet.snippet_id)

        await ctx.send("Snippet deleted.", delete_after=30, ephemeral=True)
        logger.info(f"{ctx.author} deleted the snippet with the name {name}.")

    @commands.command(
        name="forcedeletesnippet",
        aliases=["fds"],
        usage="forcedeletesnippet [name]",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def force_delete_snippet(self, ctx: commands.Context[Tux], name: str) -> None:
        """
        Force delete a snippet by name.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        name : str
            The name of the snippet.
        """

        assert ctx.guild

        snippet = await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id)

        if snippet is None:
            await self.send_snippet_error(ctx, description="Snippet not found.")
            return

        await self.db.delete_snippet_by_id(snippet.snippet_id)

        await ctx.send("Snippet deleted.", delete_after=30, ephemeral=True)
        logger.info(f"{ctx.author} force deleted the snippet with the name {name}.")

    @commands.command(
        name="snippet",
        aliases=["s"],
        usage="snippet [name]",
    )
    @commands.guild_only()
    async def get_snippet(self, ctx: commands.Context[Tux], name: str) -> None:
        """
        Get a snippet by name.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        name : str
            The name of the snippet.
        """

        assert ctx.guild

        snippet = await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id)

        # check if the name contains an underscore
        if "_" in name:
            await self.send_snippet_error(
                ctx,
                description="Did you mean to use `-` instead of `_`? Due to a recent change, `_` is no longer allowed in snippet names.",
            )
            return
        if snippet is None:
            await self.send_snippet_error(ctx, description="No snippets found.")
            return
        await self.db.increment_snippet_uses(snippet.snippet_id)

        # example text:
        # `/snippets/name.txt` [if locked put '🔒 ' icon]|| [content]
        text = f"`/snippets/{snippet.snippet_name}.txt` "
        if snippet.locked:
            text += "🔒 "
        text += f"|| {snippet.snippet_content}"

        await ctx.send(text, allowed_mentions=AllowedMentions.none())

    @commands.command(
        name="snippetinfo",
        aliases=["si"],
        usage="snippetinfo [name]",
    )
    @commands.guild_only()
    async def get_snippet_info(self, ctx: commands.Context[Tux], name: str) -> None:
        """
        Get information about a snippet by name.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        name : str
            The name of the snippet.
        """

        assert ctx.guild

        snippet = await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id)

        if snippet is None:
            await self.send_snippet_error(ctx, description="Snippet not found.")
            return

        author = self.bot.get_user(snippet.snippet_user_id)

        embed: discord.Embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.DEFAULT,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            title="Snippet Information",
            message_timestamp=snippet.snippet_created_at or datetime.datetime.fromtimestamp(0, datetime.UTC),
        )

        embed.add_field(name="Name", value=snippet.snippet_name, inline=False)
        embed.add_field(
            name="Author",
            value=f"{author.mention if author else f'<@!{snippet.snippet_user_id}>'}",
            inline=False,
        )
        embed.add_field(name="Content", value=f"> {snippet.snippet_content}", inline=False)
        embed.add_field(name="Uses", value=snippet.uses, inline=False)
        embed.add_field(name="Locked", value="Yes" if snippet.locked else "No", inline=False)

        await ctx.send(embed=embed)

    @commands.command(
        name="createsnippet",
        aliases=["cs"],
        usage="createsnippet [name] [content]",
    )
    @commands.guild_only()
    async def create_snippet(self, ctx: commands.Context[Tux], *, arg: str) -> None:
        """
        Create a snippet.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        arg : str
            The name and content of the snippet.
        """

        assert ctx.guild

        if await self.is_snippetbanned(ctx.guild.id, ctx.author.id):
            await ctx.send("You are banned from using snippets.")
            return

        args = arg.split(" ")
        if len(args) < 2:
            await self.send_snippet_error(ctx, description="Please provide a name and content for the snippet.")
            return

        name = args[0]
        content = " ".join(args[1:])
        created_at = datetime.datetime.now(datetime.UTC)
        author_id = ctx.author.id
        server_id = ctx.guild.id

        # Check if the snippet already exists
        if await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id) is not None:
            await self.send_snippet_error(ctx, description="Snippet already exists.")
            return

        # Check if the name is longer than 20 characters and includes non-alphanumeric characters (except -)
        rules = set(string.ascii_letters + string.digits + "-")

        if len(name) > 20 or any(char not in rules for char in name):
            await self.send_snippet_error(
                ctx,
                description="Snippet name must be alphanumeric (allows dashes only) and less than 20 characters.",
            )
            return

        await self.db.create_snippet(
            snippet_name=name,
            snippet_content=content,
            snippet_created_at=created_at,
            snippet_user_id=author_id,
            guild_id=server_id,
        )

        await ctx.send("Snippet created.", delete_after=30, ephemeral=True)
        logger.info(f"{ctx.author} created a snippet with the name {name}.")

    @commands.command(
        name="editsnippet",
        aliases=["es"],
        usage="editsnippet [name] [content]",
    )
    @commands.guild_only()
    async def edit_snippet(self, ctx: commands.Context[Tux], *, arg: str) -> None:
        """
        Edit a snippet.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        arg : str
            The name and content of the snippet.
        """

        assert ctx.guild

        args = arg.split(" ")
        if len(args) < 2:
            await self.send_snippet_error(ctx, description="Please provide a name and content for the snippet.")
            return

        name = args[0]
        content = " ".join(args[1:])
        author_id = ctx.author.id
        snippet = await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id)

        if snippet is None:
            await self.send_snippet_error(ctx, description="Snippet not found.")
            return

        if await self.is_snippetbanned(ctx.guild.id, ctx.author.id):
            await ctx.send("You are banned from using snippets.")
            return

        # check if the snippet is locked
        if snippet.locked:
            logger.info(
                f"{ctx.author} is trying to edit a snippet with the name {name}. Checking if they have the permission level to edit locked snippets.",
            )
            # dont make the check send its own error message
            try:
                await checks.has_pl(2).predicate(ctx)
            except commands.CheckFailure:
                await self.send_snippet_error(
                    ctx,
                    description="This snippet is locked and cannot be edited. If you are a moderator you can use the `forcedeletesnippet` command.",
                )
                return
            logger.info(f"{ctx.author} has the permission level to edit locked snippets.")

        # Check if the author of the snippet is the same as the user who wants to edit it and if theres no author don't allow editing
        author_id = snippet.snippet_user_id or 0
        if author_id != ctx.author.id:
            await self.send_snippet_error(ctx, description="You can only edit your own snippets.")
            return

        await self.db.update_snippet_by_id(
            snippet.snippet_id,
            snippet_content=content,
        )

        await ctx.send("Snippet Edited.", delete_after=30, ephemeral=True)
        logger.info(f"{ctx.author} Edited a snippet with the name {name}.")

    @commands.command(
        name="togglesnippetlock",
        aliases=["tsl"],
        usage="togglesnippetlock [name]",
    )
    @commands.guild_only()
    @checks.has_pl(2)
    async def toggle_snippet_lock(self, ctx: commands.Context[Tux], name: str) -> None:
        """
        Toggle a snippet lock.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        name : str
            The name of the snippet.
        """

        assert ctx.guild

        snippet = await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id)

        if snippet is None:
            await self.send_snippet_error(ctx, description="Snippet not found.")
            return

        status = await self.db.toggle_snippet_lock_by_id(snippet.snippet_id)

        if status is None:
            await self.send_snippet_error(
                ctx,
                "No return value from locking the snippet. It may still have been locked.",
            )
            return

        if author := self.bot.get_user(snippet.snippet_user_id):
            with contextlib.suppress(discord.Forbidden):
                await author.send(
                    f"""Your snippet `{snippet.snippet_name}` has been {'locked' if status.locked else 'unlocked'}.

**What does this mean?**
If a snippet is locked, it cannot be edited by anyone other than moderators. This means that you can no longer edit this snippet.

**Why was it locked?**
Snippets are usually locked by moderators if they are important to usual use of the server. Changes or deletions to these snippets can have a big impact on the server. If you believe this was done in error, please open a ticket with /ticket.""",
                )

        await ctx.send("Snippet lock toggled.", delete_after=30, ephemeral=True)
        logger.info(f"{ctx.author} toggled the lock of the snippet with the name {name}.")

    async def send_snippet_error(self, ctx: commands.Context[Tux], description: str) -> None:
        """
        Send an error message to the channel if there are no snippets found.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        """
        embed = EmbedCreator.create_embed(
            bot=self.bot,
            embed_type=EmbedCreator.ERROR,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
            description=description,
        )
        await ctx.send(embed=embed, delete_after=30)


async def setup(bot: Tux) -> None:
    await bot.add_cog(Snippets(bot))
