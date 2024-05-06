import discord
from discord import app_commands
from discord.ext import commands

from prisma.models import Notes
from tux.database.client import db
from tux.database.controllers import DatabaseController
from tux.utils.embeds import EmbedCreator

# look im going to be real honest with you this code is a mess and I have no idea how this ever worked.


class Note(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
        self.db_controller = DatabaseController().notes
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

    group = app_commands.Group(name="notes", description="note related commands")

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

    @group.command(name="get_all", description="Get all notes in a list.")
    async def get_all(
        self,
        interaction: discord.Interaction,
    ) -> None:
        notes = await self.get_all_notes()
        embed = EmbedCreator.create_success_embed(
            title="Success!", description="Notes obtained!", interaction=interaction
        )
        result = [(note.content, note.user_id) for note in notes]
        for i in range(len(notes)):
            embed.add_field(name="Note #: " + str(i), value=result[i][0], inline=False)
            embed.add_field(name="Note " + str(i) + "Target", value=[i][1], inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Note(bot))
