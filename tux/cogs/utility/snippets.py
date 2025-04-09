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
from tux.utils.config import Config
from tux.utils.flags import generate_usage


class Snippets(commands.Cog):
    def __init__(self, bot: Tux) -> None:
        self.bot = bot
        self.db = DatabaseController().snippet
        self.config = DatabaseController().guild_config
        self.case_controller = CaseController()
        self.list_snippets.usage = generate_usage(self.list_snippets)
        self.top_snippets.usage = generate_usage(self.top_snippets)
        self.delete_snippet.usage = generate_usage(self.delete_snippet)
        self.get_snippet.usage = generate_usage(self.get_snippet)
        self.get_snippet_info.usage = generate_usage(self.get_snippet_info)
        self.create_snippet.usage = generate_usage(self.create_snippet)
        self.edit_snippet.usage = generate_usage(self.edit_snippet)
        self.toggle_snippet_lock.usage = generate_usage(self.toggle_snippet_lock)

    async def is_snippetbanned(self, guild_id: int, user_id: int) -> bool:
        ban_cases = await self.case_controller.get_all_cases_by_type(guild_id, CaseType.SNIPPETBAN)
        unban_cases = await self.case_controller.get_all_cases_by_type(guild_id, CaseType.SNIPPETUNBAN)

        ban_count = sum(case.case_user_id == user_id for case in ban_cases)
        unban_count = sum(case.case_user_id == user_id for case in unban_cases)

        return ban_count > unban_count

    def _create_snippets_list_embed(
        self,
        ctx: commands.Context[Tux],
        snippets: list[Snippet],
        total_snippets: int,
        search_query: str | None = None,
    ) -> discord.Embed:
        """
        Create an embed for displaying a list of snippets.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        snippets : list[Snippet]
            The snippets to display on this page.
        total_snippets : int
            The total number of snippets across all pages.
        search_query : str | None
            The search query used to filter snippets (for title display).
        """
        assert ctx.guild
        assert ctx.guild.icon

        # Snippets are already filtered by the time they reach this function
        if not snippets:
            return EmbedCreator.create_embed(
                bot=self.bot,
                embed_type=EmbedType.ERROR,
                user_name=ctx.author.name,
                user_display_avatar=ctx.author.display_avatar.url,
                description="No snippets found.",
            )

        description = "```\n"

        for snippet in snippets:
            icon = "→" if snippet.alias else " "
            icon += "🔒" if snippet.locked else " "
            description += f"{icon}|{snippet.snippet_name.ljust(20)} | uses: {snippet.uses}\n"

        description += "```"

        footer_text, footer_icon_url = EmbedCreator.get_footer(
            bot=ctx.bot,
            user_name=ctx.author.name,
            user_display_avatar=ctx.author.display_avatar.url,
        )

        return EmbedCreator.create_embed(
            embed_type=EmbedType.DEFAULT,
            title=f'Snippets ({total_snippets}) | Searching for "{search_query if search_query else "All Snippets"}"',
            description=description,
            custom_author_text=ctx.guild.name,
            custom_author_icon_url=ctx.guild.icon.url,
            message_timestamp=ctx.message.created_at,
            custom_footer_text=footer_text,
            custom_footer_icon_url=footer_icon_url,
        )

    async def check_if_user_has_mod_override(self, ctx: commands.Context[Tux]) -> bool:
        try:
            await checks.has_pl(2).predicate(ctx)
        except commands.CheckFailure:
            return False
        except Exception as e:
            logger.error(f"Unexpected error in check_if_user_has_mod_override: {e}")
            return False
        else:
            return True

    async def snippet_check(
        self,
        ctx: commands.Context[Tux],
        snippet_locked: bool = False,
        snippet_user_id: int = 0,
    ) -> tuple[bool, str]:
        """
        Check if the user can create, edit, or delete snippets. This handles mod overrides, lock checks, user checks, ban checks, and role checks.
        Returns whether the user can create snippets and a reason.

        Snippet locked is only checked when editing or deleting snippets so leave it as false if you don't want to check it.
        Snippet user id is only checked when editing or deleting snippets so leave it as 0 if you don't want to check it.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        snippet_locked : bool
            Whether the snippet is locked or not. Defaults to False.
        snippet_user_id : int
            The user id of the snippet author. Defaults to 0.
        """

        assert ctx.guild

        # Check for mod override
        if await self.check_if_user_has_mod_override(ctx):
            return True, "Mod override granted."

        # Check for bans
        if await self.is_snippetbanned(ctx.guild.id, ctx.author.id):
            return False, "You are banned from using snippets."

        # Check for role permissions
        if (
            Config.LIMIT_TO_ROLE_IDS
            and isinstance(ctx.author, discord.Member)
            and not any(role.id in Config.ACCESS_ROLE_IDS for role in ctx.author.roles)
        ):
            return (
                False,
                f"You do not have a role that allows you to create snippets. Accepted roles: {format(', '.join([f'<@&{role_id}>' for role_id in Config.ACCESS_ROLE_IDS]))}",
            )

        # Check for snippet locked
        if snippet_locked:
            return False, "This snippet is locked. You cannot edit or delete it."

        # Check for snippet author
        if snippet_user_id not in (0, ctx.author.id):
            return False, "You can only edit or delete your own snippets."

        return True, "All checks passed."

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

    @commands.command(
        name="snippets",
        aliases=["ls"],
    )
    @commands.guild_only()
    async def list_snippets(self, ctx: commands.Context[Tux], *, search_query: str | None = None) -> None:
        """
        List snippets by pagination.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        search_query : str | None
            Optional search query to filter snippets.
        """
        assert ctx.guild

        # Fetch all snippets sorted by creation date
        snippets: list[Snippet] = await self.db.get_all_snippets_sorted(newestfirst=True)

        # sort by uses
        snippets.sort(key=lambda x: x.uses, reverse=True)

        # Filter snippets by guild
        snippets = [snippet for snippet in snippets if snippet.guild_id == ctx.guild.id]

        # Apply search filter if a query is provided
        if search_query:
            snippets = [
                snippet
                for snippet in snippets
                if search_query.lower() in (snippet.snippet_name or "").lower()
                or search_query.lower() in (snippet.snippet_content or "").lower()
            ]

        # If no snippets found after filtering, return early
        if not snippets:
            await self.send_snippet_error(ctx, description="No snippets found.")
            return

        # Set up pagination menu
        menu = ViewMenu(ctx, menu_type=ViewMenu.TypeEmbed)

        # Add pages based on filtered snippets
        snippets_per_page = 10
        for i in range(0, len(snippets), snippets_per_page):
            embed = self._create_snippets_list_embed(
                ctx,
                snippets[i : i + snippets_per_page],
                len(snippets),
                search_query,
            )
            menu.add_page(embed)

        # Add navigation buttons
        menu.add_button(ViewButton.go_to_first_page())
        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())
        menu.add_button(ViewButton.go_to_last_page())
        menu.add_button(ViewButton.end_session())

        await menu.start()

    @commands.command(
        name="topsnippets",
        aliases=["ts"],
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
        if not snippets:
            await self.send_snippet_error(ctx, description="No snippets found.")
            return
        snippets.sort(key=lambda x: x.uses, reverse=True)

        # Format the text
        text = "```\n"
        for i, snippet in enumerate(snippets[:10]):
            text += f"{i + 1}. {snippet.snippet_name.ljust(20)} | uses: {snippet.uses}\n"
        text += "```"

        # only show top 10, no pagination
        # TODO: add pagination
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

        # perm check
        check = await self.snippet_check(
            ctx,
            snippet_locked=snippet.locked,
            snippet_user_id=snippet.snippet_user_id,
        )
        if not check[0]:
            await self.send_snippet_error(ctx, description=check[1])
            return

        await self.db.delete_snippet_by_id(snippet.snippet_id)

        await ctx.send("Snippet deleted.", delete_after=30, ephemeral=True)
        logger.info(f"{ctx.author} deleted the snippet with the name {name}. {check[1]}")

    @commands.command(
        name="snippet",
        aliases=["s"],
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

        # check if the snippet is an alias
        if snippet.alias:
            # if it is an alias, get the snippet by name and guild id
            aliased_snippet = await self.db.get_snippet_by_name_and_guild_id(snippet.alias, ctx.guild.id)
            if aliased_snippet is None:
                # delete the alias if it points to a non-existent snippet
                await self.db.delete_snippet_by_id(snippet.snippet_id)
                await self.send_snippet_error(
                    ctx,
                    description="Alias pointing to a non-existent snippet. Deleting alias.",
                )
                return
            text = f"`{snippet.snippet_name}.txt -> {aliased_snippet.snippet_name}.txt` "
            if aliased_snippet.locked:
                text += "🔒 "
            if snippet.locked:
                text += "🔒 "
            text += f"|| {aliased_snippet.snippet_content}"
        else:
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
    )
    @commands.guild_only()
    async def create_snippet(self, ctx: commands.Context[Tux], name: str, *, content: str) -> None:
        """
        Create a snippet. You can use the name of another snippet as the content, and it will automatically create an alias to that snippet.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        name : str
            The name of the snippet.
        content : str
            The content of the snippet.
        """

        assert ctx.guild

        # perm check
        check = await self.snippet_check(ctx)
        if not check[0]:
            await self.send_snippet_error(ctx, description=check[1])
            return

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

        # check if snippet content is just the name of another snippet e.g if the content is support will auto alias to support
        snippet = await self.db.get_snippet_by_name_and_guild_id(content, ctx.guild.id)
        if snippet:
            await self.db.create_snippet_alias(
                snippet_name=name,
                snippet_alias=content,
                snippet_created_at=created_at,
                snippet_user_id=author_id,
                guild_id=server_id,
            )
            await ctx.send(
                f"Snippet created as an alias to `{content}` automatically because the content was the same as another snippet.",
                delete_after=30,
                ephemeral=True,
            )
            logger.info(f"{ctx.author} created a snippet with the name {name} as an alias to {content}.")
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
    )
    @commands.guild_only()
    async def edit_snippet(self, ctx: commands.Context[Tux], name: str, *, content: str) -> None:
        """
        Edit a snippet.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context object.
        name : str
            The name of the snippet.
        content : str
            The new content of the snippet.
        """
        assert ctx.guild

        snippet = await self.db.get_snippet_by_name_and_guild_id(name, ctx.guild.id)

        if snippet is None:
            await self.send_snippet_error(ctx, description="Snippet not found.")
            return

        # perm check
        check = await self.snippet_check(
            ctx,
            snippet_locked=snippet.locked,
            snippet_user_id=snippet.snippet_user_id,
        )
        if not check[0]:
            await self.send_snippet_error(ctx, description=check[1])
            return

        await self.db.update_snippet_by_id(
            snippet.snippet_id,
            snippet_content=content,
        )

        await ctx.send("Snippet Edited.", delete_after=30, ephemeral=True)

        logger.info(f"{ctx.author} edited the snippet with the name {name}. {check[1]}")

    @commands.command(
        name="togglesnippetlock",
        aliases=["tsl"],
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
                    f"""Your snippet `{snippet.snippet_name}` has been {"locked" if status.locked else "unlocked"}.

**What does this mean?**
If a snippet is locked, it cannot be edited by anyone other than moderators. This means that you can no longer edit this snippet.

**Why was it locked?**
Snippets are usually locked by moderators if they are important to usual use of the server. Changes or deletions to these snippets can have a big impact on the server. If you believe this was done in error, please open a ticket with /ticket.""",
                )

        await ctx.send("Snippet lock toggled.", delete_after=30, ephemeral=True)
        logger.info(f"{ctx.author} toggled the lock of the snippet with the name {name}.")


async def setup(bot: Tux) -> None:
    await bot.add_cog(Snippets(bot))
