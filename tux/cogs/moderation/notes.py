import discord
from discord import app_commands
from discord.ext import commands
from loguru import logger

from prisma.models import Notes, Users
from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator
from tux.utils.functions import datetime_to_unix


class NotesCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot
        self.db_controller: DatabaseController = DatabaseController()

    group = app_commands.Group(name="notes", description="Commands for managing notes.")

    async def get_or_create_user(self, member: discord.Member) -> None:
        """
        Retrieves a user from the database or creates a new user if not found.

        Parameters
        ----------
        member : discord.Member
            The member to retrieve or create in the database.
        """
        user: Users | None = await self.db_controller.users.get_user_by_id(user_id=member.id)

        if not user:
            await self.db_controller.users.create_user(
                user_id=member.id,
                name=member.name,
                display_name=member.display_name,
                mention=member.mention,
                bot=member.bot,
                created_at=member.created_at,
                joined_at=member.joined_at,
            )

    async def get_or_create_moderator(self, interaction: discord.Interaction) -> None:
        """
        Retrieves a moderator from the database or creates a new moderator if not found.
        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        """
        moderator: Users | None = await self.db_controller.users.get_user_by_id(interaction.user.id)

        moderator_context: discord.Member | None = (
            interaction.guild.get_member(interaction.user.id) if interaction.guild else None
        )

        if not moderator:
            await self.db_controller.users.create_user(
                user_id=interaction.user.id,
                name=interaction.user.name,
                display_name=interaction.user.display_name,
                mention=interaction.user.mention,
                bot=interaction.user.bot,
                created_at=interaction.user.created_at,
                joined_at=moderator_context.joined_at if moderator_context else None,
            )

    async def create_note(
        self, interaction: discord.Interaction, member: discord.Member, content: str
    ) -> discord.Embed:
        new_note: Notes = await self.db_controller.notes.create_note(
            user_id=member.id,
            moderator_id=interaction.user.id,
            note_content=content,
        )
        note_id: int | str = new_note.id if new_note else "Unknown"

        embed: discord.Embed = EmbedCreator.create_success_embed(
            title="",
            description="",
            interaction=interaction,
        )

        embed.set_author(
            name=f"Note #{note_id} created",
            icon_url="https://github.com/allthingslinux/tux/blob/main/assets/slicedsymbol-5.png?raw=true",
        )

        embed.add_field(name="Member", value=f"- __{member.name}__\n`{member.id}`", inline=True)
        embed.add_field(
            name="Moderator",
            value=f"- __{interaction.user.name}__\n`{interaction.user.id}`",
            inline=True,
        )

        embed.add_field(name="Content", value=f"> {content}", inline=False)

        logger.info(
            f"Note added to {member.display_name} ({member.id}) by {interaction.user.display_name}. Note: {content}"
        )

        return embed

    async def delete_note_by_id(
        self, interaction: discord.Interaction, note_id: int
    ) -> discord.Embed:
        note: Notes | None = await self.db_controller.notes.get_note_by_id(note_id)

        if not note:
            msg = "Note not found."
            raise ValueError(msg)

        await self.db_controller.notes.delete_note(note_id)

        embed: discord.Embed = EmbedCreator.create_note_embed(
            title="",
            description="",
            interaction=interaction,
        )

        member: discord.Member | None = (
            interaction.guild.get_member(note.user_id) if interaction.guild else None
        )
        moderator: discord.Member | None = (
            interaction.guild.get_member(note.moderator_id) if interaction.guild else None
        )

        moderator_name: str = moderator.display_name if moderator else "Unknown"
        member_name: str = member.display_name if member else "Unknown"
        deleted_content = note.content

        embed.set_author(
            name=f"Note #{note_id} deleted",
            icon_url="https://github.com/allthingslinux/tux/blob/main/assets/slicedsymbol-1.png?raw=true",
        )

        embed.add_field(name="Member", value=f"- {member_name}\n`{note.user_id}`", inline=True)
        embed.add_field(
            name="Moderator", value=f"- {moderator_name}\n`{note.moderator_id}`", inline=True
        )
        embed.add_field(name="Original Content", value=f"> {deleted_content}", inline=False)
        embed.add_field(
            name="Created At", value=f"{datetime_to_unix(note.created_at)}", inline=False
        )

        logger.info(f"Note ID {note_id} deleted by {interaction.user.display_name}.")

        return embed

    async def update_note_by_id(
        self, interaction: discord.Interaction, note_id: int, content: str
    ) -> discord.Embed:
        note: Notes | None = await self.db_controller.notes.get_note_by_id(note_id)

        if not note:
            msg = "Note not found."
            raise ValueError(msg)

        await self.db_controller.notes.update_note(note_id, content)

        embed: discord.Embed = EmbedCreator.create_note_embed(
            title="",
            description="",
            interaction=interaction,
        )

        member: discord.Member | None = (
            interaction.guild.get_member(note.user_id) if interaction.guild else None
        )

        moderator: discord.Member | None = (
            interaction.guild.get_member(note.moderator_id) if interaction.guild else None
        )

        member_name: str = member.display_name if member else "Unknown"
        moderator_name: str = moderator.display_name if moderator else "Unknown"
        old_content: str = note.content
        new_content: str = content

        embed.set_author(
            name=f"Note #{note_id} updated",
            icon_url="https://github.com/allthingslinux/tux/blob/main/assets/slicedsymbol-5.png?raw=true",
        )

        embed.add_field(name="Member", value=f"- {member_name}\n`{note.user_id}`", inline=True)
        embed.add_field(
            name="Moderator", value=f"- {moderator_name}\n`{note.moderator_id}`", inline=True
        )
        embed.add_field(name="Previous Content", value=f"> {old_content}", inline=False)
        embed.add_field(name="Updated Content", value=f"> {new_content}", inline=False)

        logger.info(f"Note ID {note_id} updated by {interaction.user.display_name}.")

        return embed

    async def view_note_by_id(
        self, interaction: discord.Interaction, note_id: int
    ) -> discord.Embed:
        note: Notes | None = await self.db_controller.notes.get_note_by_id(note_id)

        if not note:
            msg = "Note not found."
            raise ValueError(msg)

        embed: discord.Embed = EmbedCreator.create_note_embed(
            title="",
            description="",
            interaction=interaction,
        )

        moderator: discord.Member | None = (
            interaction.guild.get_member(note.moderator_id) if interaction.guild else None
        )
        moderator_name: str = moderator.display_name if moderator else "Unknown"

        member: discord.Member | None = (
            interaction.guild.get_member(note.user_id) if interaction.guild else None
        )

        member_name: str = member.display_name if member else "Unknown"
        note_content: str = note.content

        embed.set_author(
            name=f"Note #{note_id} viewed",
            icon_url="https://github.com/allthingslinux/tux/blob/main/assets/slicedsymbol-4.png?raw=true",
        )

        embed.add_field(name="Member", value=f"- {member_name}\n`{note.user_id}`", inline=True)
        embed.add_field(
            name="Moderator", value=f"- {moderator_name}\n`{note.moderator_id}`", inline=True
        )
        embed.add_field(name="Content", value=f"> {note_content}", inline=False)

        embed.add_field(
            name="Created At", value=f"{datetime_to_unix(note.created_at)}", inline=False
        )

        logger.info(f"Note ID {note_id} viewed by {interaction.user.display_name}.")

        return embed

    async def list_notes(
        self, interaction: discord.Interaction, member: discord.Member
    ) -> discord.Embed:
        notes: list[Notes] = await self.db_controller.notes.get_notes_by_user_id(member.id)

        description = "\n".join(
            [
                f"<:tux_note:1251209868824805426> `{note.id}`: {datetime_to_unix(note.created_at)} - <@{note.moderator_id}>"
                for note in notes
            ]
        )

        embed: discord.Embed = EmbedCreator.create_note_embed(
            title=f"All notes for {member.display_name}",
            description=description,
            interaction=interaction,
        )

        logger.info(
            f"Listed all notes for {member.display_name} by {interaction.user.display_name}."
        )

        return embed

    async def list_notes_by_moderator(
        self, interaction: discord.Interaction, moderator: discord.Member
    ) -> discord.Embed:
        notes: list[Notes] = await self.db_controller.notes.get_notes_by_moderator_id(moderator.id)

        description = "\n".join(
            [
                f"<:tux_note:1251209868824805426> `{note.id}`: {datetime_to_unix(note.created_at)} - <@{note.user_id}>"
                for note in notes
            ]
        )

        embed: discord.Embed = EmbedCreator.create_note_embed(
            title=f"All notes by {moderator.display_name}",
            description=description,
            interaction=interaction,
        )

        embed.add_field(name="Total Notes", value=f"`{len(notes)}`", inline=True)

        logger.info(
            f"Listed all notes for {moderator.display_name} by {interaction.user.display_name}."
        )

        return embed

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @group.command(name="create", description="Creates a note for a member of the server.")
    async def note_create(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        content: str,
    ) -> None:
        """
        Creates a note for a member of the server.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        member : discord.Member
            The member to add a note to.
        content : str
            The content of the note.
        """
        message = ""

        await self.get_or_create_user(member)
        await self.get_or_create_moderator(interaction)

        try:
            embed: discord.Embed = await self.create_note(interaction, member, content)
            message = f"Note added to {member.mention} by {interaction.user.mention}."

        except Exception as error:
            msg: str = f"Failed to add note for {member.display_name}. {error!s}"

            embed = EmbedCreator.create_error_embed(
                title="Note Addition Failed",
                description=msg,
                interaction=interaction,
            )

            logger.error(msg)

        await interaction.response.send_message(
            message, embed=embed, allowed_mentions=discord.AllowedMentions.none()
        )

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @group.command(name="delete", description="Deletes a note by ID.")
    async def note_delete(
        self,
        interaction: discord.Interaction,
        note_id: int,
    ) -> None:
        """
        Deletes a note by ID.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        note_id : int
            The ID of the note to delete.
        """

        try:
            embed: discord.Embed = await self.delete_note_by_id(interaction, note_id)

        except Exception as error:
            msg: str = f"Failed to delete note ID {note_id}. {error!s}"

            embed = EmbedCreator.create_error_embed(
                title="Note Deletion Failed",
                description=msg,
                interaction=interaction,
            )

            logger.error(msg)

        await interaction.response.send_message(embed=embed)

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @group.command(name="update", description="Updates a note by ID.")
    async def note_update(
        self,
        interaction: discord.Interaction,
        note_id: int,
        content: str,
    ) -> Notes | None:
        """
        Updates a note by ID.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        note_id : int
            The ID of the note to update.
        content : str
            The new content for the note.
        """
        try:
            embed: discord.Embed = await self.update_note_by_id(interaction, note_id, content)

        except Exception as error:
            msg: str = f"Failed to update note ID {note_id}. {error!s}"

            embed = EmbedCreator.create_error_embed(
                title="Note Update Failed",
                description=msg,
                interaction=interaction,
            )

            logger.error(msg)

        await interaction.response.send_message(embed=embed)

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @group.command(name="view", description="Views a note by ID.")
    async def note_view(
        self,
        interaction: discord.Interaction,
        note_id: int,
    ) -> Notes | None:
        """
        Views a note by ID.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        note_id : int
            The ID of the note to view.
        """
        try:
            embed: discord.Embed = await self.view_note_by_id(interaction, note_id)

        except Exception as error:
            msg: str = f"Failed to view note ID {note_id}. {error!s}"

            embed = EmbedCreator.create_error_embed(
                title="Note View Failed",
                description=msg,
                interaction=interaction,
            )

            logger.error(msg)

        await interaction.response.send_message(embed=embed)

    @app_commands.checks.has_any_role("Admin", "Sr. Mod", "Mod", "Jr. Mod")
    @group.command(name="list", description="Lists all notes for a member or by a moderator.")
    @app_commands.describe(
        member="The member to list notes for (optional).",
        moderator="The moderator to list notes from (optional).",
    )
    async def note_list(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
        moderator: discord.Member | None = None,
    ) -> None:
        """
        Lists all notes for a member or by a moderator.

        Parameters
        ----------
        interaction : discord.Interaction
            The interaction that triggered the command.
        member : discord.Member | None, optional
            The member to list all notes for.
        moderator : discord.Member | None, optional
            The moderator to list all notes from.
        """
        try:
            if member:
                await self.get_or_create_user(member)
                embed: discord.Embed = await self.list_notes(interaction, member)

            elif moderator:
                if interaction.guild:
                    await self.get_or_create_user(moderator)
                embed: discord.Embed = await self.list_notes_by_moderator(interaction, moderator)

            else:
                msg = "You must provide either a member or a moderator."
                raise ValueError(msg)  # noqa: TRY301

        except Exception as error:
            msg: str = f"Failed to list notes. {error!s}"
            embed = EmbedCreator.create_error_embed(
                title="Note List Failed",
                description=msg,
                interaction=interaction,
            )
            logger.error(msg)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    """Asynchronously adds the NotesCog to the bot."""
    await bot.add_cog(NotesCog(bot))
