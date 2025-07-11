from bot import Tux
from discord import AllowedMentions, Message
from discord.ext import commands
from reactionmenu import ViewButton, ViewMenu
from utils.functions import generate_usage

# from utils.functions import truncate
from . import SnippetsBaseCog


class Snippet(SnippetsBaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.snippet.usage = generate_usage(self.snippet)

    @commands.command(
        name="snippet",
        aliases=["s"],
    )
    @commands.guild_only()
    async def snippet(self, ctx: commands.Context[Tux], name: str) -> None:
        """Retrieve and display a snippet's content.

        If the snippet is an alias, it resolves the alias and displays the
        target snippet's content, indicating the alias relationship.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        name : str
            The name of the snippet to retrieve.
        """
        assert ctx.guild

        # Fetch the snippet, send error if not found
        snippet = await self._get_snippet_or_error(ctx, name)
        if not snippet:
            return

        # Increment uses before potentially resolving alias
        await self.db.snippet.increment_snippet_uses(snippet.snippet_id)

        # Handle aliases
        if snippet.alias:
            # Fetch the target snippet
            aliased_snippet = await self.db.snippet.get_snippet_by_name_and_guild_id(
                snippet.alias,
                ctx.guild.id,
            )

            # If alias target doesn't exist, delete the broken alias
            if aliased_snippet is None:
                await self.db.snippet.delete_snippet_by_id(snippet.snippet_id)

                await self.send_snippet_error(
                    ctx,
                    description=f"Alias `{snippet.snippet_name}` points to a non-existent snippet (`{snippet.alias}`). Deleting alias.",
                )
                return

            # Format message for alias
            text = f"`{snippet.snippet_name}.txt -> {aliased_snippet.snippet_name}.txt` "

            if aliased_snippet.locked:
                text += "🔒 "

            text += f"|| {aliased_snippet.snippet_content}"

        else:
            # Format message for regular snippet
            text = f"`/snippets/{snippet.snippet_name}.txt` "

            if snippet.locked:
                text += "🔒 "

            text += f"|| {snippet.snippet_content}"

        # pagination if text > 2000 characters
        if len(text) <= 2000:
            # Check if there is a message being replied to
            reference = getattr(ctx.message.reference, "resolved", None)
            # Set reply target if it exists, otherwise use the context message
            reply_target = reference if isinstance(reference, Message) else ctx

            await reply_target.reply(
                text,
                allowed_mentions=AllowedMentions(users=False, roles=False, everyone=False, replied_user=True),
            )
            return

        menu = ViewMenu(
            ctx,
            menu_type=ViewMenu.TypeText,
            all_can_click=True,
            show_page_director=False,
            timeout=180,
            delete_on_timeout=True,
        )

        for i in range(0, len(text), 2000):
            page: str = text[i : i + 2000]
            menu.add_page(content=page)

        menu.add_button(ViewButton.back())
        menu.add_button(ViewButton.next())

        await menu.start()


async def setup(bot: Tux) -> None:
    """Load the Snippet cog."""
    await bot.add_cog(Snippet(bot))
