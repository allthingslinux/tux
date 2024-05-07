import discord
from discord import app_commands
from discord.ext import commands

from prisma.models import Notes
from tux.database.client import db
from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator

# The current implementation has complexities that may hinder its functionality and maintainability.
# Assistance in refining and optimizing the code is welcome.


class Note(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.db_controller = (
            DatabaseController().notes
        )  # Define some stuff so that way I can use DB
        self.table = db.notes

    async def create_note(
        self,
        user_id: int,
        moderator_id: int,
        note_content: str,
    ) -> Notes:
        """
        Creates a new note in the database with the specified user ID, moderator ID, and content.

        Args:
            user_id (int): The ID of the user for whom the note is created.
            moderator_id (int): The ID of the moderator who created the note.
            note_content (str): The content of the note.

        Returns:
            Notes: The newly created note.
        """

        return await self.table.create(
            data={
                "user_id": user_id,
                "moderator_id": moderator_id,
                "content": note_content,
            }
        )

    async def get_all_notes(self) -> list[Notes]:
        """
        Retrieves all notes from the database.

        Returns:
            list[Notes]: A list of all notes.
        """

        return await self.table.find_many()

    async def get_note_by_user_id(self, user_id: int) -> Notes | None:
        """
        Retrieves a note from the database based on the specified user ID.

        Parameters
        ----------
        user_id : int
            The ID of the note to retrieve.

        Returns
        -------
        Notes or None
            The note if found, otherwise None.
        """
        return await self.table.find_first(where={"user_id": user_id})

    async def get_note_by_note_id(self, note_id: int) -> Notes | None:
        """
        Retrieves a note from the database based on the specified user ID.

        Parameters
        ----------
        note_id : int
            The ID of the note to retrieve.

        Returns
        -------
        Notes or None
            The note if found, otherwise None.
        """
        return await self.table.find_first(where={"id": note_id})

    async def delete_note(self, note_id: int) -> None:
        """
        Deletes a note from the database based on the specified note ID.

        Parameters
        ----------
        user_id : int
            The ID of the note to delete.

        Returns
        -------
        None
        """
        await self.table.delete(where={"id": note_id})

    async def update_note(self, note_id: int, note_content: str) -> Notes | None:
        """
        Updates a note in the database with the specified user ID and new content.

        Parameters
        ----------
        note_id : int
            The ID of the note to update.
        note_content : str
            The new content for the note.

        Returns
        -------
        Notes or None
            The updated note if successful, otherwise None if the note was not found.
        """
        return await self.table.update(
            where={"id": note_id},
            data={"content": note_content},
        )

    group = app_commands.Group(name="notes", description="note related commands")
    # Make a group so that way everything is in one nice place

    @app_commands.checks.has_any_role(
        "Root", "Admin", "Sr. Mod", "Mod", "Contributor"
    )  # Role Checking
    @group.command(name="create", description="Create a note.")
    async def create(
        self, interaction: discord.Interaction, target_member: discord.Member, note: str
    ) -> None:
        invoke_id = interaction.user.id
        await self.create_note(user_id=target_member.id, moderator_id=invoke_id, note_content=note)
        embed = EmbedCreator.create_success_embed(
            title="Success!", description="Note Created.", interaction=interaction
        )
        embed.add_field(name="Note Target", value=target_member)
        embed.add_field(name="Note Content", value=note)
        await interaction.response.send_message(embed=embed)

    @app_commands.checks.has_permissions(manage_messages=True)
    @group.command(name="get_num", description="Get x notes in a list.")
    async def get_num(
        self,
        interaction: discord.Interaction,
        num1: int,
        num2: int,
    ) -> None:
        notes = await self.get_all_notes()
        embed = EmbedCreator.create_success_embed(
            title="Success!", description="Notes obtained!", interaction=interaction
        )
        result = [(note.content, note.user_id, note.id) for note in notes]

        try:
            for i in range(num1, num2):
                embed.add_field(name=f"Note #: {i!s}", value=result[i][0], inline=False)
                embed.add_field(name=f"Note {i!s} Target", value=result[i][1], inline=False)
                embed.add_field(name=f"Note {i!s} ID: ", value=result[i][2], inline=False)
        except IndexError:
            embed = EmbedCreator.create_error_embed(
                title="Index Error", description="Out of range", interaction=interaction
            )
            embed.add_field(
                name="Error details",
                value="One of the numbers you provided is not in the notes list. "
                "try again with a valid index range.",
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.checks.has_any_role("Root", "Admin", "Sr. Mod", "Mod", "Contributor")
    @group.command(name="get_by_member", description="Obtain a note based on a certain member.")
    async def get_by_member(self, interaction: discord.Interaction, member: discord.Member) -> None:
        member_id = member.id
        note = await self.get_note_by_user_id(member_id)

        if note is None:
            embed = EmbedCreator.create_error_embed(
                title="Error", description="Note not found", interaction=interaction
            )
            embed.add_field(
                name="Error Details",
                value="Note not found! please try a different member that has a note.",
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = EmbedCreator.create_success_embed(
                title="Note Found!", interaction=interaction, description=""
            )
            embed.add_field(name="Note Target", value=str(member))
            embed.add_field(name="Note content", value=note.content)
            embed.add_field(name="Note ID", value=note.id)
            await interaction.response.send_message(embed=embed)

    @app_commands.checks.has_any_role("Root", "Admin", "Sr. Mod", "Mod", "Contributor")
    @group.command(name="delete", description="Remove a note based on note ID.")
    async def delete(
        self,
        interaction: discord.Interaction,
        note_id: int,
    ) -> None:
        note = await self.get_note_by_note_id(
            note_id=note_id
        )  # First do a check to make sure a note exists
        if note is None:
            embed = EmbedCreator.create_error_embed(title="No note found.", description="")
            embed.add_field(
                name="Error Details",
                value="No note found to delete. please provide a valid note ID.",
            )
            await interaction.response.send_message(embed=embed)
        else:
            await self.delete_note(note_id=note_id)
            embed = EmbedCreator.create_success_embed(
                title="Success!",
                description="Deleted Note " + str(note_id) + ".",
                interaction=interaction,
            )

            await interaction.response.send_message(embed=embed)

    @app_commands.checks.has_any_role("Root", "Admin", "Sr. Mod", "Mod", "Contributor")
    @group.command(name="update", description="update a note based on note ID")
    async def update(
        self,
        interaction: discord.Interaction,
        note_id: int,
        new_content: str,
    ) -> None:
        note = await self.get_note_by_note_id(
            note_id=note_id
        )  # check if there is actually a note before moving on.
        if note is None:
            embed = EmbedCreator.create_error_embed(title="No note found.", description="")
            embed.add_field(
                name="Error Details",
                value="No note found to update. please provide a valid note ID.",
            )
            await interaction.response.send_message(embed=embed)
        else:
            await self.update_note(note_id=note_id, note_content=new_content)
            embed = EmbedCreator.create_success_embed(
                title="Success!", description="Updated note " + str(note_id) + "."
            )
            embed.add_field(name="New note", value=new_content)
            await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Note(bot))
