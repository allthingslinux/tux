from bot import Tux
from discord.ext import commands
from loguru import logger
from utils.constants import CONST
from utils.functions import generate_usage

from . import SnippetsBaseCog


class EditSnippet(SnippetsBaseCog):
    def __init__(self, bot: Tux) -> None:
        super().__init__(bot)
        self.edit_snippet.usage = generate_usage(self.edit_snippet)

    @commands.command(
        name="editsnippet",
        aliases=["es"],
    )
    @commands.guild_only()
    async def edit_snippet(self, ctx: commands.Context[Tux], name: str, *, content: str) -> None:
        """Edit an existing snippet.

        Checks for ownership and lock status before editing.

        Parameters
        ----------
        ctx : commands.Context[Tux]
            The context of the command.
        name : str
            The name of the snippet to edit.
        content : str
            The new content for the snippet.
        """
        assert ctx.guild

        # Fetch the snippet, send error if not found
        snippet = await self._get_snippet_or_error(ctx, name)

        if not snippet:
            return

        # Check permissions (role, ban, lock, ownership)
        can_edit, reason = await self.snippet_check(
            ctx,
            snippet_locked=snippet.locked,
            snippet_user_id=snippet.snippet_user_id,
        )

        if not can_edit:
            await self.send_snippet_error(ctx, description=reason)
            return

        # Update the snippet content
        await self.db.snippet.update_snippet_by_id(
            snippet_id=snippet.snippet_id,
            snippet_content=content,
        )

        await ctx.send("Snippet edited.", delete_after=CONST.DEFAULT_DELETE_AFTER, ephemeral=True)

        logger.info(f"{ctx.author} edited snippet '{name}'. Override: {reason}")


async def setup(bot: Tux) -> None:
    """Load the EditSnippet cog."""
    await bot.add_cog(EditSnippet(bot))
