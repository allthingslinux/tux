import discord
from discord.ext import commands

from prisma.models import Note
from tux.utils.constants import Constants as CONST

from . import ModerationCogBase


class Notes(ModerationCogBase):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)

    @commands.hybrid_group(
        name="notes",
        aliases=["n"],
        usage="$notes <subcommand>",
    )
    @commands.guild_only()
    async def notes(self, ctx: commands.Context[commands.Bot]) -> None:
        """
        Notes related commands.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context object for the command.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send_help("notes")

    @notes.command(
        name="create",
        aliases=["c", "add", "a"],
        usage="$notes create [target] [content]",
    )
    @commands.guild_only()
    async def create_note(self, ctx: commands.Context[commands.Bot], target: discord.Member, content: str) -> None:
        """
        Create a note for a user.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        target : discord.Member
            The member to add a note to.
        content : str
            The content of the note
        """

        if ctx.guild:
            try:
                note = await self.db.note.insert_note(
                    note_target_id=target.id,
                    note_moderator_id=ctx.author.id,
                    note_content=content,
                    guild_id=ctx.guild.id,
                )

            except Exception as e:
                await ctx.reply(f"An error occurred while creating the note: {e}", delete_after=30, ephemeral=True)
                return

            await self.handle_note_response(ctx, note, "created", content, target)

    @notes.command(
        name="delete",
        aliases=["d"],
        usage="$notes delete [note_id]",
    )
    @commands.guild_only()
    async def delete_note(self, ctx: commands.Context[commands.Bot], note_id: int) -> None:
        """
        Delete a note by ID.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        note_id : int
            The ID of the note to delete

        Raises
        ------
        commands.MemberNotFound
            If the member is not found.
        commands.UserNotFound
            If the user is not found.
        """

        if ctx.guild:
            note = await self.db.note.get_note_by_id(note_id)

            if not note:
                await ctx.reply("Note not found.", delete_after=30, ephemeral=True)
                return

            await self.db.note.delete_note_by_id(note_id)

            try:
                target = await commands.MemberConverter().convert(ctx, str(note.note_target_id))
            except commands.MemberNotFound:
                target = await commands.UserConverter().convert(ctx, str(note.note_target_id))

            await self.handle_note_response(ctx, note, "deleted", note.note_content, target)

    @notes.command(
        name="update",
        aliases=["u", "edit", "e", "modify", "m"],
        usage="$notes update [note_id] [content]",
    )
    @commands.guild_only()
    async def update_note(self, ctx: commands.Context[commands.Bot], note_id: int, content: str) -> None:
        """
        Update a note by ID.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        note_id : int
            The ID of the note to update.
        content : str
            The new content for the note.

        Raises
        ------
        commands.MemberNotFound
            If the member is not found.
        commands.UserNotFound
            If the user is not found
        """

        if ctx.guild:
            note = await self.db.note.get_note_by_id(note_id)

            if not note:
                await ctx.reply("Note not found.", delete_after=30, ephemeral=True)
                return

            previous_content = note.note_content
            await self.db.note.update_note_by_id(note_id, content)

            try:
                target = await commands.MemberConverter().convert(ctx, str(note.note_target_id))
            except commands.MemberNotFound:
                target = await commands.UserConverter().convert(ctx, str(note.note_target_id))

            await self.handle_note_response(ctx, note, "updated", content, target, previous_content)

    @notes.command(
        name="view",
        aliases=["v", "get", "g"],
        usage="$notes view [note_id]",
    )
    @commands.guild_only()
    async def view_note(
        self,
        ctx: commands.Context[commands.Bot],
        note_id: int,
    ) -> None:
        """
        View a note by ID.

        Parameters
        ----------
        ctx : commands.Context[commands.Bot]
            The context in which the command is being invoked.
        note_id : int
            The ID of the note to view.

        Raises
        ------
        commands.MemberNotFound
            If the member is not found.
        commands.UserNotFound
            If the user is not found.
        """

        if ctx.guild:
            note = await self.db.note.get_note_by_id(note_id)

            if not note:
                await ctx.reply("Note not found.", delete_after=30, ephemeral=True)
                return

            try:
                target = await commands.MemberConverter().convert(ctx, str(note.note_target_id))
            except commands.MemberNotFound:
                target = await commands.UserConverter().convert(ctx, str(note.note_target_id))

            await self.handle_note_response(ctx, note, "viewed", note.note_content, target)

    async def handle_note_response(
        self,
        ctx: commands.Context[commands.Bot],
        note: Note,
        action: str,
        content: str,
        target: discord.Member | discord.User,
        previous_content: str | None = None,
    ) -> None:
        moderator = ctx.author

        fields = [
            ("Moderator", f"__{moderator}__\n`{moderator.id}`", True),
            ("Target", f"__{target}__\n`{target.id}`", True),
            ("Content", f"> {content}", False),
        ]
        if previous_content:
            fields.append(("Previous Content", f"> {previous_content}", False))

        embed = await self.create_embed(
            ctx,
            title=f"Note #{note.note_id} {action}",
            fields=fields,
            color=CONST.EMBED_COLORS["NOTE"],
            icon_url=CONST.EMBED_ICONS["NOTE"],
        )

        await self.send_embed(ctx, embed, log_type="private")
        await ctx.reply(embed=embed, delete_after=30, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Notes(bot))
